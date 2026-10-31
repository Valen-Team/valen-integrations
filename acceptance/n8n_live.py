"""Run the shipped synthetic workflow through local n8n with real Valen inference."""
import json
import os
import time
from pathlib import Path
from urllib.parse import urlsplit
import httpx
from .n8n_runtime import unflatten

ROOT = Path(__file__).resolve().parents[1]


def main():
    url = os.environ.get('VALEN_ACCEPTANCE_N8N_URL', 'http://127.0.0.1:15678')
    if urlsplit(url).hostname not in ('127.0.0.1', 'localhost', '::1'):
        raise ValueError('Use a disposable loopback n8n instance')
    client = httpx.Client(base_url=url, timeout=60)
    login = client.post('/rest/login', json={
        'emailOrLdapLoginId': os.environ['VALEN_ACCEPTANCE_N8N_EMAIL'],
        'password': os.environ['VALEN_ACCEPTANCE_N8N_PASSWORD'],
    })
    login.raise_for_status()
    credential = client.post('/rest/credentials', json={
        'name': 'Valen synthetic live acceptance', 'type': 'valenApi',
        'data': {'baseUrl': 'https://api.valen-team.workers.dev', 'apiKey': ''},
    })
    credential.raise_for_status()
    credential = credential.json()['data']
    example = json.loads((ROOT/'n8n/examples/support-routing.json').read_text())
    for node in example['nodes']:
        if node['type'] == '@valen-team/n8n-nodes-valen.valen':
            node['credentials'] = {'valenApi': {'id': credential['id'], 'name': credential['name']}}
    payload = {key: example[key] for key in ('name', 'nodes', 'connections', 'settings') if key in example}
    saved = client.post('/rest/workflows', json=payload)
    saved.raise_for_status()
    workflow_id = saved.json()['data']['id']
    started = client.post(f'/rest/workflows/{workflow_id}/run', json={'triggerToStartFrom': {'name': 'Run example'}})
    started.raise_for_status()
    execution_id = started.json()['data']['executionId']
    deadline = time.monotonic() + 420
    while True:
        response = client.get('/rest/executions/' + str(execution_id))
        response.raise_for_status()
        execution = response.json()['data']
        if execution['status'] in ('success', 'error', 'crashed', 'canceled'):
            break
        if time.monotonic() > deadline:
            raise TimeoutError(f'Live execution still pending: {execution_id}')
        time.sleep(.5)
    details = unflatten(execution['data'])
    assert execution['status'] == 'success', details['resultData'].get('error')
    runs = details['resultData']['runData']
    assert 'Request failure' not in runs
    destinations = {}
    for name, branch in [('Billing', 'billing'), ('Technical', 'technical'), ('Human review', 'review')]:
        items = runs[name][0]['data']['main'][0]
        assert len(items) == 1
        value = items[0]['json']
        assert value['ticket'] and value['valen']['branch'] == branch
        assert value['valen']['model'] == 'valen-2b'
        destinations[name] = value
    report = {'workflow_id': workflow_id, 'execution_id': execution_id, 'status': 'passed',
              'scope': 'Shipped synthetic workflow; real local n8n engine and free Valen API',
              'destinations': destinations}
    (ROOT/'validation/n8n-live.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report), flush=True)
    client.close()


if __name__ == '__main__':
    main()
