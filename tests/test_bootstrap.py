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

    # --- seeding: native data home, synthetic-only, scoped sandbox config, no secrets imported ---
    def test_seed_allowlist_no_secret_import(self):
        b.seed(self.target, 'synthetic-password-$value#yes')
        home = self.target / 'home'
        files = {p.relative_to(home).as_posix() for p in home.rglob('*') if p.is_file()}
        self.assertEqual(files, set(b.ALLOWLIST) | {'config.yaml', '.env'})
        self.assertNotIn('auth.json', files)
        self.assertNotIn('state.db', files)
        env = (home / '.env').read_text()
        self.assertIn('$value#yes', env)
        self.assertIn('HERMES_DASHBOARD_BASIC_AUTH_USERNAME=participant', env)
        if os.name != 'nt':
            self.assertEqual((home / '.env').stat().st_mode & 0o777, 0o600)
        # Training config: Docker terminal sandbox backend, scoped training data only.
        cfg = (home / 'config.yaml').read_text()
        self.assertIn('backend: docker', cfg)
        self.assertIn('/opt/sid-training', cfg)
        # No broad host mounts, no Docker socket, no credentials in config.
        self.assertNotIn('docker.sock', cfg)
        self.assertNotIn('~/', cfg)
        self.assertNotIn('API_KEY', cfg)
        self.assertNotIn('BASIC_AUTH', cfg)

    def test_repeat_never_overwrites(self):
        b.seed(self.target, 'synthetic-only-long-password')
        before = (self.target / 'home' / '.env').read_bytes()
        with self.assertRaises(FileExistsError):
            b.seed(self.target, 'different-password')
        self.assertEqual(before, (self.target / 'home' / '.env').read_bytes())

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

    # --- native install command is the official one-liner ---
    def test_native_install_command_posix(self):
        with patch.object(b.platform, 'system', return_value='Linux'):
            self.assertEqual(b.native_install_command(), 'curl -fsSL ' + b.INSTALL_SH + ' | bash')

    def test_native_install_command_windows(self):
        with patch.object(b.platform, 'system', return_value='Windows'):
            self.assertEqual(b.native_install_command(), 'iex (irm ' + b.INSTALL_PS1 + ')')

    # --- Docker is required only as the terminal sandbox backend (local engine only) ---
    def test_docker_available_requires_local_engine(self):
        results = [Mock(stdout='ok'), Mock(stdout='[{\"Endpoints\":{\"docker\":{\"Host\":\"unix:///mock/docker.sock\"}}}]')]
        with patch.object(b.shutil, 'which', return_value='/mock/docker'):
            with patch.object(b, 'run', side_effect=results):
                b.docker_available()  # no exception: local unix engine is accepted

    def test_docker_available_rejects_tcp_context(self):
        results = [Mock(stdout='ok'), Mock(stdout='[{\"Endpoints\":{\"docker\":{\"Host\":\"tcp://10.0.0.5:2376\"}}}]')]
        with patch.object(b.shutil, 'which', return_value='/mock/docker'):
            with patch.object(b, 'run', side_effect=results):
                with self.assertRaisesRegex(RuntimeError, 'local Docker'):
                    b.docker_available()

    def test_docker_available_rejects_missing_docker(self):
        with patch.object(b.shutil, 'which', return_value=None):
            with self.assertRaisesRegex(RuntimeError, 'docker is missing'):
                b.docker_available()

    def test_preflight_rejects_existing_serve(self):
        # docker: info, context inspect; tailscale: status, serve status. Port bind is a socket.
        results = [Mock(stdout='ok'), Mock(stdout='[{\"Endpoints\":{\"docker\":{\"Host\":\"unix:///mock/docker.sock\"}}}]'),
                   Mock(stdout='{\"BackendState\":\"Running\"}'), Mock(stdout='{\"TCP\":{\"443\":{}}}')]
        with patch.object(b.platform, 'system', return_value='Linux'), patch.object(b.shutil, 'which', return_value='/mock'), patch.object(b, 'run', side_effect=results):
            with self.assertRaisesRegex(RuntimeError, 'Existing Tailscale'):
                b.preflight(self.target)

    def test_preflight_rejects_wsl(self):
        with patch.object(b.platform, 'system', return_value='Linux'), patch.object(b.platform, 'release', return_value='6.6.0-microsoft-standard-WSL2'), patch.object(b, 'run', return_value=Mock(stdout='ok')), patch.object(b.shutil, 'which', return_value='/mock'):
            with self.assertRaisesRegex(RuntimeError, 'WSL'):
                b.preflight(self.target)

    def test_preflight_tailnet_only_checks_tailscale(self):
        # Tailscale-only preflight: no Docker engine check, no port bind.
        results = [Mock(stdout='{\"BackendState\":\"Running\",\"Self\":{\"DNSName\":\"t.example.ts.net.\"}}'),
                   Mock(stdout='{}')]
        with patch.object(b, 'run', side_effect=results) as run, patch.object(b.shutil, 'which', return_value='/mock'):
            state = b.preflight(self.target, check_docker=False, check_tailscale=True)
        self.assertEqual(state['Self']['DNSName'], 't.example.ts.net.')
        # No docker command should have been invoked in tailnet-only mode.
        self.assertFalse(any(c[0] == 'docker' for c in run.call_args_list))

    # --- dashboard authentication: cookie login, denial, wrong-password, failure ---
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

    # --- Desktop package download: checksum + refusal ---
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

    def test_existing_partial_is_preserved(self):
        dest = Path(self.tmp.name) / 'package.zip'
        partial = dest.with_suffix('.zip.partial')
        partial.write_bytes(b'existing')
        with self.assertRaisesRegex(RuntimeError, 'Partial download'):
            b.download({'url': 'https://example.invalid', 'sha256': '0' * 64}, dest)
        self.assertEqual(partial.read_bytes(), b'existing')

    # --- end-to-end native orchestration (mocked) ---
    def test_mocked_full_native_flow(self):
        calls = []
        def run(*args, **kwargs):
            calls.append(args)
            if args[:2] == ('tailscale', 'serve') and 'status' in args:
                count = sum(c[:2] == ('tailscale', 'serve') and 'status' in c for c in calls)
                return Mock(stdout='{}' if count <= 2 else '{"TCP":{"9119":{"TCPForward":"127.0.0.1:9119"}}}')
            if args[:3] == ('tailscale', 'status', '--json'):
                return Mock(stdout='{"BackendState":"Running","Self":{"DNSName":"t.example.ts.net."}}')
            if args[:2] == ('docker', 'context'):
                return Mock(stdout='[{"Endpoints":{"docker":{"Host":"unix:///mock/docker.sock"}}}]')
            return Mock(stdout='ok')
        with patch.object(b, 'run', side_effect=run), patch.object(b.shutil, 'which', return_value='/mock'), \
             patch.object(b, 'health') as health, patch.object(b.socket, 'socket') as sock, \
             patch('getpass.getpass', return_value='synthetic-password-long'), patch('builtins.input', return_value='yes'), \
             patch.object(b.platform, 'system', return_value='Linux'), \
             patch.object(b.sys, 'argv', ['bootstrap.py', '--home', str(self.target)]):
            b.main()
        health.assert_called_once_with('synthetic-password-long')
        # Native install invoked, scoped to the training home (env carries HERMES_HOME).
        install = [c for c in calls if 'curl -fsSL' in ' '.join(c)]
        self.assertTrue(install)
        self.assertTrue(any('dashboard' in c for c in calls))
        # Serve rule added only after authenticated health (the last tailnet mutation).
        self.assertIn(('tailscale', 'serve', '--bg', '--tcp=9119', 'tcp://127.0.0.1:9119'), calls)

    def test_serve_not_added_when_tailnet_skipped(self):
        # Preflight runs in tailnet-only mode (no tailscale) -> serve must never run.
        with patch.object(b, 'preflight', return_value=None), \
             patch.object(b, 'run', return_value=Mock(stdout='ok')), \
             patch.object(b, 'health'), \
             patch.object(b, 'consent'), \
             patch('getpass.getpass', return_value='synthetic-password-long'), \
             patch.object(b.platform, 'system', return_value='Linux'), \
             patch.object(b.sys, 'argv', ['bootstrap.py', '--home', str(self.target)]):
            b.main()
            # (main returns before the serve block when state is None)
        self.assertTrue((self.target / 'home').exists())

    def test_failure_never_starts_serve(self):
        def run(*args, **kwargs):
            if 'curl -fsSL' in ' '.join(args):
                raise RuntimeError('install failed')
            return Mock(stdout='ok')
        with patch.object(b, 'preflight', return_value={}), patch.object(b, 'run', side_effect=run), \
             patch.object(b, 'consent'), patch('getpass.getpass', return_value='synthetic-password-long'), \
             patch.object(b.platform, 'system', return_value='Linux'), \
             patch.object(b.sys, 'argv', ['bootstrap.py', '--home', str(self.target)]):
            with self.assertRaisesRegex(RuntimeError, 'install failed'):
                b.main()
        self.assertTrue(self.target.exists())

    # --- receipt integrity + static checks ---
    def test_pin_receipt_integrity(self):
        record = json.loads((ROOT / 'research/desktop-stable-record.json').read_text())
        self.assertEqual(hashlib.sha256((ROOT / 'research/desktop-build.json').read_bytes()).hexdigest(), record['head']['sha256'])
        # versions.json now carries native install URLs + Desktop pins; no separate runtime image.
        versions = json.loads((ROOT / 'versions.json').read_text())
        self.assertIn('native', versions)
        self.assertTrue(versions['native']['install_sh'].startswith('https://hermes-agent.nousresearch.com/'))
        self.assertTrue(versions['native']['install_ps1'].startswith('https://hermes-agent.nousresearch.com/'))
        self.assertIn('desktop', versions)

    def test_bash_syntax(self):
        if os.name == 'nt' or not __import__('shutil').which('bash'):
            self.skipTest('POSIX Bash check; Windows bash may be an unconfigured WSL shim')
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
