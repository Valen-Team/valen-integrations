"""Confirm a real hosted-limit error reaches Dify's failure destination."""
import copy
import json
from pathlib import Path
import yaml
from .dify_client import DifyClient

ROOT = Path(__file__).resolve().parents[1]


def main():
    client = DifyClient()
    document = (ROOT/'dify/examples/support-review.yml').read_text()
    imported = client.http.post('/console/api/apps/imports', json={
        'mode': 'yaml-content', 'yaml_content': document, 'name': 'Valen limit acceptance'})
    imported.raise_for_status()
    app = imported.json()['app_id']
    original = yaml.safe_load(document)['workflow']
    workflow = copy.deepcopy(original)
    tool = next(n['data'] for n in workflow['graph']['nodes'] if n['data']['type'] == 'tool')
    tool.update(tool_name='evaluate', tool_label='Evaluate', tool_configurations={})
    tool['tool_parameters'] = {
        'input': {'type': 'mixed', 'value': 'Synthetic limit test'},
        'model': {'type': 'mixed', 'value': 'valen-2b'},
        'questions': {'type': 'mixed', 'value': json.dumps([
            {'name': f'q{i}', 'type': 'predicate', 'instructions': 'A synthetic judgment.'} for i in range(9)])},
    }
    try:
        client.save(app, workflow)
        events = client.run(app, {'ticket': 'Synthetic limit test'})
        final = events[-1]
        output = final['data']['outputs']
        assert final['data']['status'] == 'partial-succeeded', final
        message = output['failure_error_message']
        assert 'HTTP 400' in message and '8' in message and 'request ID:' in message, output
        assert not any(key.endswith('_probability') for key in output)
        report = {'status': 'passed', 'app_id': app, 'final': final}
        (ROOT/'validation/dify-limits.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report), flush=True)
    finally:
        client.save(app, original)
        client.http.close()


if __name__ == '__main__':
    main()
