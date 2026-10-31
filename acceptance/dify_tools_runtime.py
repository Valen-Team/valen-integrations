"""Run with python -m acceptance.dify_tools_runtime against disposable local Dify."""
import copy
import json
from pathlib import Path
import yaml
from .dify_client import DifyClient

ROOT = Path(__file__).resolve().parents[1]
CASES = [
    ('choice', {'options': 'billing: Payments and duplicate charges\ntech: Software errors\nreview: Other or unclear requests'},
     [('branch', 'string'), ('choice', 'string'), ('confidence', 'number'),
      ('probabilities', 'object'), ('model', 'string')]),
    ('score', {'levels': 'low: No urgency or deadline\nmedium: Needs help soon\nhigh: Needs immediate help'},
     [('branch', 'string'), ('level', 'string'), ('score', 'number'),
      ('confidence', 'number'), ('probabilities', 'object'), ('model', 'string')]),
    ('evaluate', {'questions': json.dumps([{'name': 'refund', 'type': 'predicate',
                                          'instructions': 'The customer requests a refund.'}])},
     [('json', 'array[object]')]),
]


def tool_workflow(original, name, extra, fields):
    workflow = copy.deepcopy(original)
    nodes = workflow['graph']['nodes']
    start = next(node for node in nodes if node['data']['type'] == 'start')
    tool = next(node for node in nodes if node['data']['type'] == 'tool')
    end = next(node for node in nodes if node['id'] == 'valen-refund')
    data = tool['data']
    data.update(tool_name=name, tool_label=name, title=name, tool_configurations={})
    data.pop('paramSchemas', None)
    values = {'input': '{{#' + start['id'] + '.ticket#}}', 'model': 'valen-2b', **extra}
    if name != 'evaluate':
        values['question'] = 'Which team should handle this ticket?' if name == 'choice' else 'How urgent is this ticket?'
    data['tool_parameters'] = {key: {'type': 'mixed', 'value': value} for key, value in values.items()}
    end['data']['outputs'] = [{'variable': key, 'value_type': kind, 'value_selector': [tool['id'], key]}
                             for key, kind in fields]
    edges = workflow['graph']['edges']
    workflow['graph']['nodes'] = [start, tool, end]
    workflow['graph']['edges'] = [
        edges[0],
        dict(edges[1], target=end['id'], id=tool['id'] + '-source-' + end['id'],
             data={'sourceType': 'tool', 'targetType': 'end'}),
    ]
    return workflow


def main():
    client = DifyClient()
    document = (ROOT/'dify/examples/support-review.yml').read_text()
    response = client.http.post('/console/api/apps/imports', json={
        'mode': 'yaml-content', 'yaml_content': document, 'name': 'Valen four-tool acceptance'})
    response.raise_for_status()
    imported = response.json()
    assert imported['status'] == 'completed' and not imported['warnings'], imported
    app = imported['app_id']
    original = yaml.safe_load(document)['workflow']
    results = []
    try:
        for name, extra, fields in CASES:
            client.save(app, tool_workflow(original, name, extra, fields))
            events = client.run(app, {'ticket': 'I was charged twice. Please refund the duplicate charge.'})
            final = events[-1]
            assert final['event'] == 'workflow_finished' and final['data']['status'] == 'succeeded', final
            output = final['data']['outputs']
            assert output, final
            if name == 'choice':
                assert output['choice'] == output['branch'] == 'billing'
            elif name == 'score':
                assert output['branch'] == output['level'] and 0 <= output['score'] <= 2
            else:
                assert 'refund' in output['json'][0]['answers']
            results.append({'tool': name, 'final': final})
            print(name + ': passed', flush=True)
    finally:
        try:
            client.save(app, original)
        finally:
            (ROOT/'validation/dify-tools.json').write_text(json.dumps(results, indent=2) + '\n')
            client.http.close()


if __name__ == '__main__':
    main()
