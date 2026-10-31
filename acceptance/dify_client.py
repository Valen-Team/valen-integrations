"""Official console endpoints for the disposable local Dify acceptance instance."""
import base64
import json
import os
from urllib.parse import urlsplit
import httpx


class DifyClient:
    def __init__(self):
        url=os.environ.get('VALEN_ACCEPTANCE_DIFY_URL','http://127.0.0.1:18980').rstrip('/')
        if urlsplit(url).hostname not in ('127.0.0.1','localhost','::1'):
            raise ValueError('Use a disposable loopback Dify instance')
        self.http=httpx.Client(base_url=url,timeout=180)
        r=self.http.post('/console/api/login',json={
            'email':os.environ['VALEN_ACCEPTANCE_DIFY_EMAIL'],
            'password':base64.b64encode(os.environ['VALEN_ACCEPTANCE_DIFY_PASSWORD'].encode()).decode(),
            'remember_me':True,
        })
        r.raise_for_status()
        for name in self.http.cookies.keys():
            if 'csrf' in name.lower(): self.http.headers['X-CSRF-Token']=self.http.cookies.get(name)

    def export(self,app):
        r=self.http.get(f'/console/api/apps/{app}/export',params={'format':'yaml','include_secret':'false'})
        r.raise_for_status();return r.json()['data']

    def save(self,app,workflow):
        r=self.http.get(f'/console/api/apps/{app}/workflows/draft');r.raise_for_status()
        latest=r.json()
        payload={'graph':workflow['graph'],'features':workflow['features'],'conversation_variables':workflow.get('conversation_variables',[]),'hash':latest['hash']}
        r=self.http.post(f'/console/api/apps/{app}/workflows/draft',json=payload)
        r.raise_for_status();return r.json()

    def run(self,app,inputs,files=None):
        events=[]
        with self.http.stream('POST',f'/console/api/apps/{app}/workflows/draft/run',json={'inputs':inputs,'files':files or []}) as r:
            r.raise_for_status()
            for line in r.iter_lines():
                if line.startswith('data:'):
                    event=json.loads(line[5:]);events.append(event)
                    if event.get('event') in ('workflow_finished', 'error'):
                        break
        return events
