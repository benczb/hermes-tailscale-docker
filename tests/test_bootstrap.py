import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch, Mock
import urllib.error

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('bootstrap', ROOT / 'bootstrap.py')
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR'))
        self.addCleanup(self.tmp.cleanup)
        self.target = Path(self.tmp.name) / 'training'

    def test_seed_allowlist_no_secret_import(self):
        b.seed(self.target, 'synthetic-password-$value#yes')
        files = {str(p.relative_to(self.target / 'data')) for p in (self.target / 'data').rglob('*') if p.is_file()}
        self.assertEqual(files, set(b.ALLOWLIST))
        self.assertNotIn('auth.json', files)
        self.assertIn('$value#yes', (self.target / 'runtime.env').read_text())
        if os.name != 'nt':
            self.assertEqual((self.target / 'runtime.env').stat().st_mode & 0o777, 0o600)
        text = (self.target / 'compose.yaml').read_text()
        self.assertIn('127.0.0.1:9119:9119', text)
        self.assertIn('format: raw', text)
        self.assertNotIn('docker.sock', text)
        self.assertNotIn(':latest', text)

    def test_repeat_never_overwrites(self):
        b.seed(self.target, 'synthetic-only-long-password')
        before = (self.target / 'runtime.env').read_bytes()
        with self.assertRaises(FileExistsError):
            b.seed(self.target, 'different-password')
        self.assertEqual(before, (self.target / 'runtime.env').read_bytes())

    def test_existing_preflight_has_no_external_effects(self):
        self.target.mkdir()
        with patch.object(b, 'run') as run:
            with self.assertRaisesRegex(RuntimeError, 'already exists'):
                b.preflight(self.target)
            run.assert_not_called()

    def test_declined_consent(self):
        with patch('builtins.input', return_value='no'):
            with self.assertRaisesRegex(RuntimeError, 'Declined'):
                b.consent('Proceed?')

    def test_health_checks_denial_and_cookie_login(self):
        responses = [(401, None), (401, None), (200, {'ok': True}), (200, {'status': 'ready'})]
        with patch.object(b, 'request', side_effect=responses) as request:
            b.health('synthetic-password', attempts=1)
        self.assertEqual(request.call_count, 4)
        self.assertEqual(request.call_args_list[2].args[1], '/auth/password-login')
        self.assertEqual(request.call_args_list[2].args[2]['provider'], 'basic')
        self.assertIsNot(request.call_args_list[0].args[0], request.call_args_list[2].args[0])

    def test_health_rejects_open_api(self):
        with patch.object(b, 'request', return_value=(200, {})):
            with self.assertRaisesRegex(RuntimeError, 'anonymous'):
                b.health('synthetic-password', attempts=1)

    def test_health_rejects_bad_password_accepted(self):
        with patch.object(b, 'request', side_effect=[(401, None), (200, {})]):
            with self.assertRaisesRegex(RuntimeError, 'Incorrect password'):
                b.health('synthetic-password', attempts=1)

    def test_health_timeout_is_failure(self):
        with patch.object(b, 'request', side_effect=urllib.error.URLError('offline')):
            with self.assertRaisesRegex(RuntimeError, 'did not become ready'):
                b.health('synthetic-password', attempts=1)

    def test_verified_download_and_bad_hash(self):
        payload = b'synthetic download'
        artifact = {'url': 'https://example.invalid/package', 'sha256': hashlib.sha256(payload).hexdigest()}
        dest = Path(self.tmp.name) / 'package.zip'
        with patch('urllib.request.urlopen', return_value=io.BytesIO(payload)):
            b.download(artifact, dest)
        self.assertEqual(dest.read_bytes(), payload)
        dest.unlink()
        artifact['sha256'] = '0' * 64
        with patch('urllib.request.urlopen', return_value=io.BytesIO(payload)):
            with self.assertRaisesRegex(RuntimeError, 'checksum'):
                b.download(artifact, dest)
        self.assertFalse(dest.exists())
        self.assertFalse(dest.with_suffix('.zip.partial').exists())

    def test_preflight_rejects_existing_serve(self):
        results = [Mock(stdout='ok'), Mock(stdout='[{"Endpoints":{"docker":{"Host":"unix:///mock/docker.sock"}}}]'), Mock(stdout='ok'), Mock(stdout='[]'), Mock(stdout='{"BackendState":"Running"}'), Mock(stdout='{"TCP":{"443":{}}}')]
        with patch.object(b.platform, 'system', return_value='Linux'), patch.object(b.shutil, 'which', return_value='/mock'), patch.object(b, 'run', side_effect=results):
            with self.assertRaisesRegex(RuntimeError, 'Existing Tailscale'):
                b.preflight(self.target)

    def test_mocked_full_runtime_flow(self):
        calls = []
        def run(*args, **kwargs):
            calls.append(args)
            if args[:3] == ('docker', 'compose', 'ls'):
                return Mock(stdout='[]')
            if args[:3] == ('docker', 'context', 'inspect'):
                return Mock(stdout='[{"Endpoints":{"docker":{"Host":"unix:///mock/docker.sock"}}}]')
            if args[:3] == ('tailscale', 'status', '--json'):
                return Mock(stdout='{"BackendState":"Running","Self":{"DNSName":"test.example.ts.net."}}')
            if args[:4] == ('tailscale', 'serve', 'status', '--json'):
                count = sum(c[:4] == args[:4] for c in calls)
                return Mock(stdout='{}' if count <= 2 else '{"TCP":{"9119":{"TCPForward":"127.0.0.1:9119"}}}')
            return Mock(stdout='2.30.3')
        with patch.object(b, 'run', side_effect=run), patch.object(b.shutil, 'which', return_value='/mock'), patch.object(b, 'health') as health, patch.object(b.socket, 'socket') as sock, patch('getpass.getpass', return_value='synthetic-password-long'), patch('builtins.input', return_value='yes'), patch.object(b.sys, 'argv', ['bootstrap.py', '--directory', str(self.target)]):
            b.main()
        health.assert_called_once_with('synthetic-password-long')
        self.assertIn(('tailscale', 'serve', '--bg', '--tcp=9119', 'tcp://127.0.0.1:9119'), calls)
        self.assertTrue(any('setup' in c for c in calls))
        self.assertTrue(any('up' in c for c in calls))

    def test_failure_never_starts_serve(self):
        with patch.object(b, 'preflight', return_value={}), patch.object(b, 'run', return_value=Mock(stdout='2.30.3')), patch.object(b, 'compose', side_effect=RuntimeError('pull failed')) as compose, patch.object(b, 'consent'), patch('getpass.getpass', return_value='synthetic-password-long'), patch.object(b.sys, 'argv', ['bootstrap.py', '--directory', str(self.target)]):
            with self.assertRaisesRegex(RuntimeError, 'pull failed'):
                b.main()
        self.assertTrue(self.target.exists())
        self.assertEqual(compose.call_count, 1)

    def test_existing_partial_is_preserved(self):
        dest = Path(self.tmp.name) / 'package.zip'
        partial = dest.with_suffix('.zip.partial')
        partial.write_bytes(b'existing')
        with self.assertRaisesRegex(RuntimeError, 'Partial download'):
            b.download({'url': 'https://example.invalid', 'sha256': '0' * 64}, dest)
        self.assertEqual(partial.read_bytes(), b'existing')

    def test_cookie_auth_over_real_local_http(self):
        from http.server import BaseHTTPRequestHandler, HTTPServer
        import threading
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass
            def do_GET(self):
                ok = self.headers.get('Cookie') == 'session=synthetic'
                self.send_response(200 if ok else 401)
                self.end_headers()
                self.wfile.write(b'{"status":"ready"}' if ok else b'{}')
            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                ok = body.get('password') == 'synthetic-password-long'
                self.send_response(200 if ok else 401)
                if ok:
                    self.send_header('Set-Cookie', 'session=synthetic; Path=/; HttpOnly')
                self.end_headers()
                self.wfile.write(b'{"ok":true}' if ok else b'{}')
        server = HTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with patch.object(b, 'BASE', 'http://127.0.0.1:' + str(server.server_port)):
                b.health('synthetic-password-long', attempts=1)
        finally:
            server.shutdown()
            thread.join()
            server.server_close()

    def test_preflight_rejects_existing_project(self):
        results = [Mock(stdout='ok'), Mock(stdout='[{"Endpoints":{"docker":{"Host":"unix:///mock/docker.sock"}}}]'), Mock(stdout='ok'), Mock(stdout='[{"Name":"sid-training"}]')]
        with patch.object(b.platform, 'system', return_value='Linux'), patch.object(b.shutil, 'which', return_value='/mock'), patch.object(b, 'run', side_effect=results):
            with self.assertRaisesRegex(RuntimeError, 'project already exists'):
                b.preflight(self.target)

    def test_pin_receipt_integrity(self):
        record = json.loads((ROOT / 'research/desktop-stable-record.json').read_text())
        self.assertEqual(hashlib.sha256((ROOT / 'research/desktop-build.json').read_bytes()).hexdigest(), record['head']['sha256'])
        self.assertRegex(b.pins()['runtime']['image'], r'v0\.22\.2@sha256:[0-9a-f]{64}$')

    def test_bash_syntax(self):
        if not __import__('shutil').which('bash'):
            self.skipTest('bash absent')
        subprocess.run(['bash', '-n', str(ROOT / 'bootstrap.sh')], check=True)

    def test_profile_frontmatter_and_public_file_policy(self):
        text = (ROOT / 'profile/skills/sid-board-review/SKILL.md').read_text()
        self.assertTrue(text.startswith('---\nname: sid-board-review\n'))
        self.assertIn('\ndescription:', text)
        for path in (ROOT / 'profile').rglob('*'):
            self.assertFalse(path.is_symlink())
            self.assertNotIn(path.name, ('.env', 'auth.json', 'state.db', 'config.yaml'))


if __name__ == '__main__':
    unittest.main()
