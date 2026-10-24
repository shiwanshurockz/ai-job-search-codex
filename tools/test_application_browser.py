"""Local-only browser integration check: fill and upload, never click Submit.
Run with bundled Python after installing tools/browser dependencies.
"""
import json
import os
import queue
import re
import shutil
import subprocess
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = b'''<!doctype html><title>Application test</title>
<form method="post" action="/submit">
<label>Full name<input name="name" required></label>
<label>Email<input name="email" type="email" required></label>
<button type="button" onclick="document.getElementById('cv').click()">Upload resume</button>
<input id="cv" name="cv" type="file" hidden onchange="document.getElementById('uploaded').textContent=this.files[0].name">
<p id="uploaded"></p><button type="submit">Submit application</button></form>'''


class Handler(BaseHTTPRequestHandler):
    submitted = 0
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(HTML)
    def do_POST(self):
        Handler.submitted += 1
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Submitted')
    def log_message(self, *args):
        pass


def run():
    node = shutil.which('node') or str(Path.home() / '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe')
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    with tempfile.TemporaryDirectory(dir=ROOT / '.local-tools') as temp:
        temp = Path(temp)
        pdf = temp / 'test-resume.pdf'
        pdf.write_bytes(b'%PDF-1.7\nLocal upload test only')
        cmd = [node, str(ROOT / 'tools/browser/node_modules/@playwright/mcp/cli.js'),
               '--browser', 'chrome', '--headless', '--isolated', '--no-webmcp',
               '--output-dir', str(temp)]
        proc = subprocess.Popen(cmd, cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True, encoding='utf-8')
        messages, errors = queue.Queue(), []
        def read_stdout():
            for line in proc.stdout:
                try: messages.put(json.loads(line))
                except json.JSONDecodeError: pass
        def read_stderr():
            for line in proc.stderr:
                errors.append(line)
        threading.Thread(target=read_stdout, daemon=True).start()
        threading.Thread(target=read_stderr, daemon=True).start()
        serial = 0
        def rpc(method, params, notification=False):
            nonlocal serial
            serial += 1
            request = {'jsonrpc': '2.0', 'method': method, 'params': params}
            if not notification: request['id'] = serial
            proc.stdin.write(json.dumps(request) + '\n'); proc.stdin.flush()
            if notification: return
            while True:
                try: response = messages.get(timeout=45)
                except queue.Empty: raise RuntimeError('MCP timeout: ' + ''.join(errors)[-1000:])
                if response.get('id') == serial:
                    if 'error' in response: raise RuntimeError(response['error'])
                    result = response['result']
                    if result.get('isError'): raise RuntimeError(result)
                    return result
        def call(name, args):
            result = rpc('tools/call', {'name': name, 'arguments': args})
            text = '\n'.join(c.get('text', '') for c in result.get('content', []))
            for saved in re.findall(r'\[Snapshot\]\(([^)]+)\)', text):
                path = (ROOT / saved).resolve()
                if not path.is_relative_to(ROOT):
                    raise AssertionError('Unexpected snapshot path')
                text += '\n' + path.read_text(encoding='utf-8')
            return text
        def ref(snapshot, role, label):
            match = re.search(re.escape(role + ' "' + label + '"') + r'[^\n]*?\[ref=([^\]]+)\]', snapshot)
            if not match: raise AssertionError('Missing element ' + label + '\n' + snapshot)
            return match.group(1)
        try:
            rpc('initialize', {'protocolVersion': '2024-11-05', 'capabilities': {},
                               'clientInfo': {'name': 'application-local-test', 'version': '1'}})
            rpc('notifications/initialized', {}, notification=True)
            tool_defs = rpc('tools/list', {})['tools']
            names = {t['name'] for t in tool_defs}
            assert {'browser_navigate', 'browser_fill_form', 'browser_file_upload'} <= names
            snapshot = call('browser_navigate', {'url': f'http://127.0.0.1:{server.server_port}/'})
            snapshot = call('browser_fill_form', {'fields': [
                {'name': 'Full name', 'target': ref(snapshot, 'textbox', 'Full name'), 'type': 'textbox', 'value': 'Test Applicant'},
                {'name': 'Email', 'target': ref(snapshot, 'textbox', 'Email'), 'type': 'textbox', 'value': 'test@example.test'}]})
            snapshot = call('browser_snapshot', {})
            call('browser_click', {'element': 'Upload resume', 'target': ref(snapshot, 'button', 'Upload resume')})
            call('browser_file_upload', {'paths': [str(pdf)]})
            final = call('browser_snapshot', {})
            assert 'Test Applicant' in final and 'test@example.test' in final, final
            assert 'test-resume.pdf' in final, final
            assert Handler.submitted == 0, 'Unexpected submission before review'
            call('browser_close', {})
            print('PASS: MCP startup, real Chrome form fill, file upload, readback, and zero submissions before review.')
        finally:
            proc.terminate()
            try: proc.wait(timeout=10)
            except subprocess.TimeoutExpired: proc.kill(); proc.wait()
            server.shutdown()


if __name__ == '__main__':
    run()
