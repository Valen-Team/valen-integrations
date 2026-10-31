"""Exercise generated Coze Python with real Valen HTTP; this is NOT Coze cloud acceptance."""
import importlib.util
import json
import os
import sys
import types
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(tool):
    runtime = types.ModuleType('runtime')
    runtime.Args = type('Args', (), {'__class_getitem__': classmethod(lambda cls, _: cls)})
    typing = types.ModuleType(f'typings.{tool}.{tool}')
    typing.Input = typing.Output = dict
    sys.modules.update({'runtime': runtime, 'typings': types.ModuleType('typings'),
                        f'typings.{tool}': types.ModuleType(f'typings.{tool}'),
                        f'typings.{tool}.{tool}': typing})
    spec = importlib.util.spec_from_file_location(f'coze_{tool}', ROOT/f'coze/tools/{tool}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.API_KEY = Path(os.environ['VALEN_API_KEY_FILE']).read_text().strip()
    return module


def main():
    cases = [
        ('yes_no', {'question': 'The customer requests a refund.'}),
        ('choice', {'question': 'Which team should handle this ticket?',
                    'options': 'billing: Payments and refunds\ntech: Software errors\nreview: Other or unclear requests'}),
        ('score', {'question': 'How urgent is this ticket?',
                   'levels': 'low: No urgency or deadline\nmedium: Needs help soon\nhigh: Needs immediate help'}),
        ('evaluate', {'questions': json.dumps([{'name': 'refund', 'type': 'predicate',
                                                'instructions': 'The customer requests a refund.'}])}),
    ]
    results = []
    for tool, params in cases:
        module = load(tool)
        args = types.SimpleNamespace(input=types.SimpleNamespace(
            input='I was charged twice. Please refund the duplicate charge.', image='', **params))
        answer = module.handler(args)
        assert answer['model'] == 'valen-2b', answer
        if tool == 'yes_no':
            assert answer['branch'] == 'yes' and .7 <= answer['probability'] <= 1
        elif tool == 'choice':
            assert answer['choice'] == answer['branch'] == 'billing'
            assert abs(sum(answer['probabilities'].values()) - 1) < .001
        elif tool == 'score':
            assert answer['branch'] == answer['level'] and 0 <= answer['score'] <= 2
        else:
            assert .7 <= answer['answers']['refund']['probability'] <= 1
        results.append({'tool': tool, 'status': 'passed', 'answer': answer})
        print(tool + ': passed', flush=True)
    png = (ROOT/'tests/assets/red-square.png').read_bytes()
    class Image(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-Type', 'image/png')
            self.end_headers()
            self.wfile.write(png)
    server = ThreadingHTTPServer(('127.0.0.1', 0), Image)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        answer = load('yes_no').handler(types.SimpleNamespace(input=types.SimpleNamespace(
            input='Inspect the attached image.', question='The image shows a red square.',
            image=f'http://127.0.0.1:{server.server_port}/red-square.png')))
        assert answer['branch'] == 'yes' and answer['probability'] >= .7, answer
        results.append({'tool': 'image', 'status': 'passed', 'answer': answer})
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
    try:
        load('evaluate').handler(types.SimpleNamespace(input=types.SimpleNamespace(
            input='Synthetic limit test', image='', questions=json.dumps([
                {'name': f'q{i}', 'type': 'predicate', 'instructions': 'A synthetic judgment.'} for i in range(9)]))))
    except RuntimeError as error:
        message = str(error)
        assert 'HTTP 400' in message and '8' in message and 'request ' in message, message
        results.append({'tool': 'hosted-limit', 'status': 'passed', 'error': message})
    else:
        raise AssertionError('Hosted service unexpectedly accepted nine questions')
    report = {'scope': 'Local Python with stubbed Coze runtime types, real keyed API HTTP; not cloud acceptance',
              'cases': results}
    (ROOT/'validation/coze-local-live.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
