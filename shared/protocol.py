"""Platform-neutral Valen workflow rules. Vendored by scripts/build_shared.py."""
import base64
import json
import math
import re
from urllib.parse import urlsplit


def endpoint(value):
    parts = urlsplit(value)
    if parts.scheme not in ('http', 'https') or not parts.netloc or parts.username or parts.password or parts.query or parts.fragment:
        raise ValueError('Base URL must be HTTP(S), without credentials, query or fragment')
    return value.rstrip('/').removesuffix('/v1') + '/v1'


def parse_lines(text):
    result = []
    for line in str(text or '').splitlines():
        if not line.strip():
            continue
        value, sep, description = line.strip().partition(': ')
        value, description = value.strip(), description.strip() if sep else value.strip()
        if not value or not description:
            raise ValueError('Options and descriptions must not be empty')
        result.append((value, description))
    if len(result) < 2 or len({p[0] for p in result}) != len(result):
        raise ValueError('Use at least two distinct options or levels')
    return result


def validate_questions(value):
    rows = json.loads(value) if isinstance(value, str) else value
    if not isinstance(rows, list) or not rows:
        raise ValueError('Use a nonempty questions array')
    names = set()
    for q in rows:
        if not isinstance(q, dict) or not isinstance(q.get('name'), str) or not re.fullmatch(r'[A-Za-z0-9_]+', q['name']) or q['name'] in names:
            raise ValueError('Question IDs must be unique letters, digits or underscores')
        names.add(q['name'])
        if not isinstance(q.get('instructions'), str) or not q['instructions'].strip():
            raise ValueError('Each question needs instructions')
        if q.get('type') not in ('predicate', 'choice', 'score'):
            raise ValueError('Question type must be predicate, choice or score')
        if q['type'] != 'predicate':
            field, key = ('choices', 'value') if q['type'] == 'choice' else ('levels', 'label')
            values = q.get(field)
            if not isinstance(values, list) or len(values) < 2:
                raise ValueError('Use at least two distinct, described choices or levels')
            for v in values:
                if not isinstance(v, dict) or not isinstance(v.get(key), str) or not v[key].strip() or not isinstance(v.get('description'), str) or not v['description'].strip():
                    raise ValueError('Each choice or level needs a nonempty value and description')
            if len({v[key] for v in values}) != len(values):
                raise ValueError('Choice values or level labels must be distinct')
    return rows


def single_question(kind, instructions, lines=''):
    q = {'name': 'q', 'type': kind, 'instructions': instructions}
    if kind in ('choice', 'score'):
        key = 'value' if kind == 'choice' else 'label'
        q['choices' if kind == 'choice' else 'levels'] = [{key: v, 'description': d} for v, d in parse_lines(lines)]
    return validate_questions([q])[0]


def thresholds(yes_at=0.7, no_at=0.3):
    if not all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in (yes_at, no_at)) or not 0 <= no_at < yes_at <= 1:
        raise ValueError('Thresholds must satisfy 0 ≤ No at < Yes at ≤ 1')
    return yes_at, no_at


def probability(value):
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError('API returned an invalid probability')
    return value


def map_answers(response, asked):
    rows = response.get('answers') if isinstance(response, dict) else None
    if not isinstance(rows, list) or len(rows) != len(asked):
        raise ValueError('API returned an incomplete answer list')
    mapped = {}
    for q in asked:
        matches = [a for a in rows if isinstance(a, dict) and a.get('name') == q['name']]
        if len(matches) != 1 or matches[0].get('type') != q['type']:
            raise ValueError('API returned a missing, duplicate or wrong-type answer')
        a = matches[0]
        if q['type'] == 'predicate':
            mapped[q['name']] = {'probability': probability(a.get('probability'))}
            continue
        key = 'value' if q['type'] == 'choice' else 'label'
        labels = [p[key] for p in q['choices' if q['type'] == 'choice' else 'levels']]
        values = a.get('probabilities')
        if not isinstance(values, list) or len(values) != len(labels):
            raise ValueError('API returned incomplete probabilities')
        distribution = {}
        for v in values:
            label = v.get(key) if isinstance(v, dict) else None
            if label not in labels or label in distribution:
                raise ValueError('API returned unknown or duplicate candidates')
            distribution[label] = probability(v.get('probability'))
        if abs(sum(distribution.values()) - 1) > 0.001:
            raise ValueError('API probabilities do not sum to one')
        answer = {'confidence': probability(a.get('confidence')), 'probabilities': distribution}
        if q['type'] == 'choice':
            if a.get('choice') not in labels:
                raise ValueError('API returned an unknown choice')
            answer['choice'] = a['choice']
        else:
            score = a.get('score')
            if not isinstance(score, (int, float)) or isinstance(score, bool) or not math.isfinite(score) or not 0 <= score <= len(labels)-1:
                raise ValueError('API returned an invalid score')
            answer.update(score=score, level=max(labels, key=distribution.get))
        mapped[q['name']] = answer
    model = response.get('model_id') or response.get('model')
    if not isinstance(model, str) or not model:
        raise ValueError('API returned no model ID')
    return {'answers': mapped, 'model': model}


def route_answer(answer, kind, yes_at=0.7, no_at=0.3):
    thresholds(yes_at, no_at)
    if kind == 'predicate':
        branch = 'yes' if answer['probability'] >= yes_at else 'no' if answer['probability'] <= no_at else 'unsure'
    else:
        branch = answer['choice' if kind == 'choice' else 'level']
    return dict(answer, branch=branch)


def image_type(data):
    if data[:8] == b'\x89PNG\r\n\x1a\n':
        return 'image/png'
    if data[:3] == b'\xff\xd8\xff':
        return 'image/jpeg'
    if data[:4] == b'RIFF' and data[8:12] == b'WEBP':
        return 'image/webp'
    raise ValueError('Image must be PNG, JPEG or WebP')


def api_error_message(error):
    """Preserve SDK metadata when a platform only displays exception text."""
    status = getattr(error, 'status_code', None)
    request_id = getattr(error, 'request_id', None)
    message = (f'HTTP {status}: ' if status is not None else '') + str(error)
    if request_id:
        message += f' (request ID: {request_id})'
    if status == 429:
        message += '; wait at least a minute before trying again'
    return message


def evidence(value, image=None):
    if not isinstance(value, str):
        if not isinstance(value, (dict, list)):
            raise ValueError('Input must be text, a JSON object or array')
        value = json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)
    if image is None:
        return value
    if not isinstance(image, bytes):
        raise ValueError('Image must be file bytes; download remote files before calling')
    data_url = 'data:' + image_type(image) + ';base64,' + base64.b64encode(image).decode('ascii')
    return [{'role': 'user', 'content': [{'type': 'input_text', 'text': value}, {'type': 'input_image', 'image_url': data_url}]}]
