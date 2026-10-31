"""Run the installed node through an isolated n8n server, not a mocked execute context.

Requires a disposable, already initialized local n8n with the Valen package installed.
Only loopback targets are accepted. Credentials come from environment variables.
"""
import base64
import copy
import json
import os
import socket
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
import httpx

ROOT = Path(__file__).resolve().parents[1]


def unflatten(value):
    if not isinstance(value, str):
        return value
    pool = json.loads(value)
    cache = {}
    def item(index):
        if index in cache: return cache[index]
        raw = pool[index]
        if isinstance(raw, dict):
            target = cache[index] = {}
            target.update({k: child(v) for k, v in raw.items()})
        elif isinstance(raw, list):
            target = cache[index] = []
            target.extend(child(v) for v in raw)
        else:
            target = cache[index] = raw
        return target
    def child(raw):
        if isinstance(raw, str): return item(int(raw))
        if isinstance(raw, list): return [child(v) for v in raw]
        if isinstance(raw, dict): return {k: child(v) for k, v in raw.items()}
        return raw
    return item(0)


def main():
    url = os.environ.get('VALEN_ACCEPTANCE_N8N_URL', 'http://127.0.0.1:15678').rstrip('/')
    if urlsplit(url).hostname not in ('127.0.0.1', 'localhost', '::1'):
        raise SystemExit('Run only against a disposable loopback n8n instance')
    client = httpx.Client(base_url=url, timeout=60)
    response = client.post('/rest/login', json={
        'emailOrLdapLoginId': os.environ['VALEN_ACCEPTANCE_N8N_EMAIL'],
        'password': os.environ['VALEN_ACCEPTANCE_N8N_PASSWORD'],
    })
    response.raise_for_status()
    state = {'requests': [], 'mode': 'normal'}
    class Fixture(BaseHTTPRequestHandler):
        def log_message(self, *args): pass
        def do_GET(self):
            self.send_response(200); self.send_header('Content-Type','application/json'); self.end_headers()
            self.wfile.write(b'{"data":[{"id":"valen-fixture"}]}')
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            state['requests'].append(body)
            mode = state['mode']
            if mode == 'network':
                self.connection.shutdown(socket.SHUT_RDWR); self.connection.close(); return
            if mode == 'timeout':
                time.sleep(125)
                return
            status = {'unauthorized':401, 'bad-request':400, 'rate-limit':429}.get(mode, 503 if mode == 'retry' and len(state['requests']) < 3 else 200)
            if status != 200:
                payload = {'detail': 'Synthetic ' + str(status) + ' for acceptance'}
            else:
                rows = []
                for q in body['questions']:
                    answer = {'name': q['name'], 'type': q['type']}
                    if q['type'] == 'predicate': answer['probability'] = {'yes': .7, 'no': .3}.get(mode, .5)
                    elif q['type'] == 'choice':
                        answer.update(choice=q['choices'][1]['value'], confidence=.8,
                            probabilities=[{'value':v['value'],'probability':float(i==1)} for i,v in enumerate(q['choices'])])
                    else:
                        answer.update(score=1.0, confidence=0.0,
                            probabilities=[{'label':v['label'],'value':i,'probability':.5 if i in (0,2) else 0.0} for i,v in enumerate(q['levels'])])
                    rows.append(answer)
                payload = {'model_id': 'valen-fixture-v1', 'answers': [] if mode == 'malformed' else rows}
            self.send_response(status); self.send_header('Content-Type','application/json'); self.send_header('x-request-id','fixture-request-123'); self.end_headers()
            self.wfile.write(json.dumps(payload).encode())
    server = ThreadingHTTPServer(('127.0.0.1', 0), Fixture)
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    fixture_url = f'http://127.0.0.1:{server.server_port}'
    r = client.post('/rest/credentials', json={'name':'Valen acceptance fixture','type':'valenApi','data':{'baseUrl':fixture_url,'apiKey':''}})
    r.raise_for_status(); credential = r.json()['data']
    report = {'platform':'n8n','complete':False,'fixture':'controlled localhost HTTP responses; not a model benchmark','cases':[]}
    image = base64.b64encode((ROOT/'tests/assets/red-square.png').read_bytes()).decode()
    base = {'operation':'route','model':'valen-fixture','inputFormat':'item','questionType':'predicate','question':'A concrete synthetic judgment.','yesAt':.7,'noAt':.3}
    cases = [
        ('yes-boundary','yes',{},0), ('no-boundary','no',{},1), ('uncertain','normal',{},2),
        ('choice','normal',{'questionType':'choice','options':'billing: Payments\nreview: Outside payments'},1),
        ('score-tie','normal',{'questionType':'score','options':'low\nmedium\nhigh'},0),
        ('evaluate-image','normal',{'operation':'evaluate','imageField':'data','questions':json.dumps([
            {'name':'visible','type':'predicate','instructions':'A red square is visible.'},
            {'name':'team','type':'choice','instructions':'Choose a team.','choices':[{'value':'billing','description':'Payments'},{'value':'review','description':'Other requests'}]},
        ])},0),
        ('unauthorized','unauthorized',{},3), ('malformed-answer','malformed',{},3), ('transient-retries','retry',{},2),
        ('bad-request','bad-request',{},3), ('rate-limit','rate-limit',{},3),
        ('bad-thresholds','normal',{'yesAt':.2,'noAt':.7},3),
        ('unsupported-image','invalid-image',{'imageField':'data'},3),
        ('connection-reset','network',{},3), ('request-timeout','timeout',{},3),
        ('question-limit','bad-request',{'operation':'evaluate','questions':json.dumps([
            {'name':f'q{i}','type':'predicate','instructions':'A synthetic judgment.'} for i in range(9)
        ])},1),
    ]
    selected = os.environ.get('VALEN_ACCEPTANCE_CASES')
    if selected:
        names = set(selected.split(','))
        cases = [case for case in cases if case[0] in names]
        if {case[0] for case in cases} != names:
            raise ValueError('Unknown acceptance case')
        report['scope'] = 'Selected cases: ' + selected
    report['planned_case_count'] = len(cases)
    try:
        for name, mode, changes, expected in cases:
            state.update(mode=mode, requests=[])
            params = dict(base, **changes)
            count = 1 if params['operation']=='evaluate' else 2 if params['questionType']=='choice' else 3
            trigger = {'id':'start','name':'Start','type':'n8n-nodes-base.manualTrigger','typeVersion':1,'position':[0,0],'parameters':{}}
            js = 'return '+json.dumps([{'json':{'synthetic':True,'case':name}, **({'binary':{'data':{'data':image,'mimeType':'image/gif' if mode=='invalid-image' else 'image/png','fileName':'red-square.png'}}} if params.get('imageField') else {})}])+';'
            data = {'id':'input','name':'Input','type':'n8n-nodes-base.code','typeVersion':2,'position':[200,0],'parameters':{'jsCode':js}}
            judge = {'id':'judge','name':'Judge','type':'@valen-team/n8n-nodes-valen.valen','typeVersion':1,'position':[400,0],'parameters':params,'onError':'continueErrorOutput','credentials':{'valenApi':{'id':credential['id'],'name':credential['name']}}}
            sinks = [{'id':f'sink-{i}','name':f'Output {i}','type':'n8n-nodes-base.noOp','typeVersion':1,'position':[600,i*120],'parameters':{}} for i in range(count+1)]
            connections = {'Start':{'main':[[{'node':'Input','type':'main','index':0}]]},'Input':{'main':[[{'node':'Judge','type':'main','index':0}]]},'Judge':{'main':[[{'node':s['name'],'type':'main','index':0}] for s in sinks]}}
            workflow = {'name':'Valen acceptance — '+name,'nodes':[trigger,data,judge,*sinks],'connections':connections,'settings':{'executionOrder':'v1'}}
            r = client.post('/rest/workflows',json=workflow); r.raise_for_status(); saved = r.json()['data']
            r = client.post(f"/rest/workflows/{saved['id']}/run", json={'triggerToStartFrom':{'name':'Start'}})
            r.raise_for_status(); execution_id = r.json()['data']['executionId']
            deadline = time.monotonic()+(420 if mode=='timeout' else 90)
            while True:
                r = client.get('/rest/executions/'+str(execution_id)); r.raise_for_status(); execution = r.json()['data']
                if execution['status'] in ('success','error','crashed','canceled'): break
                if time.monotonic()>deadline: raise TimeoutError('Acceptance execution timed out: '+name)
                time.sleep(.5)
            details = unflatten(execution['data'])
            runs = details['resultData']['runData']
            assert execution['status']=='success', (name,details['resultData'].get('error'))
            reached = [i for i,sink in enumerate(sinks) if sink['name'] in runs]
            assert reached==[expected], (name,reached,expected)
            item = runs[f'Output {expected}'][0]['data']['main'][0][0]
            assert item['json']['synthetic'] is True
            assert item['pairedItem'] is not None
            if expected == count:
                assert item['json']['details']['input']['synthetic'] is True
                assert 'error' in item['json'] and 'valen' not in item['json']
                if mode=='unauthorized': assert '401' in item['json']['error']
            else:
                assert item['json']['valen']['model']=='valen-fixture-v1'
            if params.get('imageField') and mode!='invalid-image':
                assert state['requests'][0]['input'][0]['content'][1]['image_url'].startswith('data:image/png;base64,')
            if mode in ('retry','rate-limit','network','timeout'): assert len(state['requests'])==3
            if name in ('bad-thresholds','unsupported-image'): assert len(state['requests'])==0
            if mode=='rate-limit': assert 'minute' in item['json']['error']
            if mode=='bad-request': assert '400' in item['json']['error'] and len(state['requests'])==1
            if name=='question-limit': assert len(state['requests'][0]['questions'])==9
            report['cases'].append({'name':name,'status':'passed','execution_id':execution_id,'workflow_id':saved['id'],'output_index':expected,'api_attempts':len(state['requests'])})
            print(name+': passed',flush=True)
        report['complete'] = True
    finally:
        server.shutdown(); server.server_close(); thread.join(); client.close()
        target = Path(os.environ.get('VALEN_ACCEPTANCE_REPORT',str(ROOT/'validation/n8n-runtime.json')))
        target.write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__': main()
