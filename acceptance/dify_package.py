"""Install the local package in disposable Dify; credentials are synthetic test fixtures."""
import hashlib
import json
import os
import time
from pathlib import Path
from .dify_client import DifyClient

ROOT = Path(__file__).resolve().parents[1]


def main():
    package = Path(os.environ['VALEN_ACCEPTANCE_DIFY_PACKAGE'])
    content = package.read_bytes()
    client = DifyClient()
    uploaded = client.http.post('/console/api/workspaces/current/plugin/upload/pkg',
                               files={'pkg': (package.name, content, 'application/octet-stream')})
    uploaded.raise_for_status()
    identifier = uploaded.json()['unique_identifier']
    if not identifier.startswith('valen-team/valen:'):
        raise ValueError('This acceptance installer only replaces Valen')
    listed = client.http.get('/console/api/workspaces/current/plugin/list', params={'page': 1, 'page_size': 256})
    listed.raise_for_status()
    current = next((p for p in listed.json()['plugins'] if p['plugin_id'] == 'valen-team/valen'), None)
    if current and current['plugin_unique_identifier'] != identifier:
        removed = client.http.post('/console/api/workspaces/current/plugin/uninstall', json={
            'plugin_installation_id': current['installation_id'], 'preserve_credentials': True,
        })
        removed.raise_for_status()
    installed = client.http.post('/console/api/workspaces/current/plugin/install/pkg', json={
        'plugin_unique_identifiers': [identifier],
    })
    installed.raise_for_status()
    task_id = installed.json().get('task_id')
    if task_id:
        deadline = time.monotonic() + 180
        while True:
            response = client.http.get('/console/api/workspaces/current/plugin/tasks/' + task_id)
            response.raise_for_status()
            task = response.json()['task']
            if task['status'] == 'success':
                break
            if task['status'] in ('failed', 'failure') or time.monotonic() > deadline:
                raise RuntimeError(task)
            time.sleep(1)
    listed = client.http.get('/console/api/workspaces/current/plugin/list', params={'page': 1, 'page_size': 256})
    listed.raise_for_status()
    actual = next(p['plugin_unique_identifier'] for p in listed.json()['plugins'] if p['plugin_id'] == 'valen-team/valen')
    assert actual == identifier, (actual, identifier)
    report = {'plugin_unique_identifier': identifier, 'package_sha256': hashlib.sha256(content).hexdigest(),
              'task_id': task_id, 'status': 'installed'}
    (ROOT/'validation/dify-package.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report), flush=True)
    client.http.close()


if __name__ == '__main__':
    main()
