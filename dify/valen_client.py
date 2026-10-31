"""Dify adapter. Rules are vendored from the shared protocol; SDK owns API retries."""
import httpx
from valen_sdk import Valen
from valen_sdk.errors import ValenAPIError
from valen_protocol import api_error_message, endpoint, evidence, map_answers, route_answer, single_question, thresholds, validate_questions

USER_AGENT = {'User-Agent': 'valen-dify/0.1.0'}


def validate_credentials(credentials):
    base = endpoint(credentials['base_url'])
    headers = dict(USER_AGENT)
    if credentials.get('api_key'):
        headers['Authorization'] = 'Bearer ' + credentials['api_key']
    response = httpx.get(base + '/models', headers=headers, timeout=120)
    response.raise_for_status()
    data = response.json()
    if not isinstance(data.get('data'), list):
        raise ValueError('Server did not return a model list')


def invoke(credentials, operation, params):
    yes_at = .7 if params.get('yes_at') is None else params['yes_at']
    no_at = .3 if params.get('no_at') is None else params['no_at']
    if operation == 'evaluate':
        asked = validate_questions(params['questions'])
    else:
        kind = {'yes_no': 'predicate', 'choice': 'choice', 'score': 'score'}[operation]
        thresholds(yes_at, no_at)
        asked = [single_question(kind, params['question'], params.get('options', params.get('levels', '')))]
    image = params.get('image')
    if image:
        if image.mime_type not in ('image/png', 'image/jpeg', 'image/webp'):
            raise ValueError('Image must be PNG, JPEG or WebP')
        # Dify's file abstraction resolves signed/internal file URLs and caches its blob.
        image = image.blob
    payload = {'input': evidence(params['input'], image), 'questions': asked, 'model': params.get('model') or 'valen-2b'}
    with Valen.remote(endpoint(credentials['base_url']), api_key=credentials.get('api_key') or None,
                      timeout=120, max_retries=2, headers=USER_AGENT) as client:
        try:
            mapped = map_answers(client.predict(payload), asked)
        except ValenAPIError as error:
            raise RuntimeError(api_error_message(error)) from error
    if operation == 'evaluate':
        return mapped
    return dict(route_answer(mapped['answers']['q'], kind, yes_at, no_at), model=mapped['model'])
