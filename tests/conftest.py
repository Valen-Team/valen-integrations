"""A local HTTP fixture. These replies test integration behavior, not model accuracy."""
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import pytest


@pytest.fixture
def api():
    state = {'requests': [], 'response': None, 'status': 200}
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args): pass
        def do_GET(self):
            self.send_response(200); self.send_header('Content-Type','application/json'); self.end_headers()
            self.wfile.write(json.dumps({'data':[{'id':'valen-2b'}]}).encode())
        def do_POST(self):
            data = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            state['requests'].append({'path':self.path, 'body':data, 'headers':dict(self.headers)})
            response = state['response']
            if response is None:
                rows=[]
                for q in data['questions']:
                    if q['type']=='predicate': rows.append({'name':q['name'],'type':'predicate','probability':.5})
                    elif q['type']=='choice': rows.append({'name':q['name'],'type':'choice','choice':q['choices'][0]['value'],'confidence':1.0,'probabilities':[{'value':v['value'],'probability':float(i==0)} for i,v in enumerate(q['choices'])]})
                    else: rows.append({'name':q['name'],'type':'score','score':1.0,'confidence':0.0,'probabilities':[{'label':v['label'],'value':i,'probability':.5 if i in (0,len(q['levels'])-1) else 0.0} for i,v in enumerate(q['levels'])]})
                response={'model_id':'valen-fixture','answers':rows}
            self.send_response(state['status']); self.send_header('Content-Type','application/json'); self.send_header('x-request-id','fixture-123'); self.end_headers()
            self.wfile.write(json.dumps(response).encode())
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    state['url']=f'http://127.0.0.1:{server.server_port}'
    yield state
    server.shutdown();server.server_close();thread.join()
