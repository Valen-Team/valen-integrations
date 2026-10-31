"""Import the distributable example and exercise real Dify execution with synthetic data.

Run as ``python -m acceptance.dify_runtime`` with the acceptance login environment.
Uses the configured Valen provider in the disposable local Dify workspace.
"""
import copy
import json
from pathlib import Path
import yaml
from .dify_client import DifyClient

ROOT = Path(__file__).resolve().parents[1]


def main():
    client = DifyClient()
    document = (ROOT / 'dify/examples/support-review.yml').read_text()
    original = yaml.safe_load(document)['workflow']
    response = client.http.post('/console/api/apps/imports', json={
        'mode': 'yaml-content', 'yaml_content': document, 'name': 'Valen runtime acceptance',
    })
    response.raise_for_status()
    imported = response.json()
    assert imported['status'] == 'completed' and not imported['warnings'], imported
    app = imported['app_id']
    report = {'platform': 'Dify', 'app_id': app, 'complete': False, 'cases': []}
    try:
        for name, ticket, destination in [
            ('yes', 'Please refund the duplicate charge.', 'Refund queue'),
            ('no', 'How do I reset my password?', 'Normal support'),
            ('unsure', 'How do I reset my password?', 'Human review'),
            ('api-error', 'How do I reset my password?', 'Request failure'),
            ('image', 'Inspect the attached image.', 'Refund queue'),
        ]:
            workflow = copy.deepcopy(original)
            tool = next(n['data'] for n in workflow['graph']['nodes'] if n['data']['type'] == 'tool')
            inputs = {'ticket': ticket}
            if name == 'unsure':
                # Exercise the configured middle band without tuning wording to a result.
                tool['tool_configurations']['yes_at']['value'] = .99
                tool['tool_configurations']['no_at']['value'] = .01
            elif name == 'api-error':
                tool['tool_parameters']['model']['value'] = 'valen-invalid-acceptance-model'
            elif name == 'image':
                tool['tool_parameters']['question']['value'] = 'The image shows a red square.'
                uploaded = client.http.post('/console/api/files/upload', files={
                    'file': ('red-square.png', (ROOT/'tests/assets/red-square.png').read_bytes(), 'image/png'),
                })
                uploaded.raise_for_status()
                inputs['image'] = {'type': 'image', 'transfer_method': 'local_file', 'upload_file_id': uploaded.json()['id']}
            client.save(app, workflow)
            events = client.run(app, inputs)
            final = events[-1]
            assert final['event'] == 'workflow_finished', final
            finished = [e['data'] for e in events if e['event'] == 'node_finished']
            ends = [n['title'] for n in finished if n['node_type'] == 'end']
            assert ends == [destination], (name, ends, final)
            raw_outputs = final['data']['outputs']
            prefix = {'Refund queue': 'refund_', 'Normal support': 'support_',
                      'Human review': 'review_', 'Request failure': 'failure_'}[destination]
            assert all(key.startswith(prefix) for key in raw_outputs), raw_outputs
            outputs = {key.removeprefix(prefix): value for key, value in raw_outputs.items()}
            assert outputs['ticket'] == ticket
            if name == 'api-error':
                assert final['data']['status'] == 'partial-succeeded'
                assert any(f'HTTP {status}' in outputs['error_message'] for status in (400, 403)), outputs
                assert 'request ID:' in outputs['error_message'], outputs
                assert 'probability' not in outputs and 'branch' not in outputs
            else:
                assert final['data']['status'] == 'succeeded', final
                assert outputs['model'] == 'valen-2b' and 0 <= outputs['probability'] <= 1
                assert outputs['branch'] == ('yes' if name == 'image' else name), outputs
            report['cases'].append({'name': name, 'status': 'passed', 'destination': destination,
                                    'run_id': final['workflow_run_id'], 'outputs': raw_outputs})
            print(name + ': passed', flush=True)
        report['complete'] = True
    finally:
        client.save(app, original)
        (ROOT/'validation/dify-runtime.json').write_text(json.dumps(report, indent=2) + '\n')
        client.http.close()


if __name__ == '__main__':
    main()
