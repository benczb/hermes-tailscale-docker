#!/usr/bin/env python3
"""Offline regression checks; real applications are never installed by these tests."""
import html
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('sync', ROOT / 'scripts/sync-profile-template.py')
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)

MOCK = r'''#!/usr/bin/env python3
import json, os, pathlib, sys
name = pathlib.Path(sys.argv[0]).name
args = sys.argv[1:]
home = pathlib.Path(os.environ['HOME'])
with open(os.environ['MOCK_LOG'], 'a') as f:
    f.write(json.dumps([name] + args) + '\n')
if name == 'hermes' and os.environ.get('HERMES_HOME'):
    sys.exit(77)  # Never let installer/backend commands select an inherited custom home.
if name == 'id': print('1000')
elif name == 'uname': print(os.environ['MOCK_OS'] if args == ['-s'] else 'arm64')
elif name == 'docker':
    if os.environ.get('MOCK_FAIL') == 'docker': sys.exit(1)
    if '--format' in args: print('linux')
elif name == 'tailscale':
    if args == ['ip', '-4']: print('100.80.90.10')
elif name == 'sudo':
    import subprocess
    sys.exit(subprocess.call(args))
elif name == 'curl':
    if '--write-out' in args:
        busy = os.environ.get('MOCK_FAIL') in ('occupied-port', 'explicit-busy') and 'http://127.0.0.1:9119' in args
        print('9119' if busy else '0', end='')
    elif '-o' in args:
        target = pathlib.Path(args[args.index('-o') + 1])
        if target.name == 'hermes-install.sh':
            target.write_text('#!/bin/bash\nif [ "$MOCK_OS" = Darwin ]; then [ "$OPENSSL_DIR" = /mock/homebrew/opt/openssl@3 ] && [[ "$PKG_CONFIG_PATH" = "$OPENSSL_DIR/lib/pkgconfig"* ]] || exit 78; fi\ncp "$MOCK_HERMES_SOURCE" "$MOCK_BIN/hermes"\nchmod 755 "$MOCK_BIN/hermes"\nmkdir -p "$HOME/.hermes"\n')
        else:
            target.write_text('name: workshop\n')
    else: print('{"auth_required": %s}' % ('false' if os.environ.get('MOCK_FAIL') == 'auth' else 'true'))
elif name == 'brew' and args == ['--prefix', 'openssl@3']: print('/mock/homebrew/opt/openssl@3')
elif name == 'openssl': print('a' * (int(args[-1]) * 2))
elif name == 'hermes':
    if args[:2] == ['profile', 'install']:
        profile = args[args.index('--name') + 1]
        target = home / '.hermes/profiles' / profile
        target.mkdir(parents=True)
        (target / '.env').write_text('EXISTING_KEY=preserved\n')
    elif 'HERMES_DASHBOARD_BASIC_AUTH_PASSWORD' in args:
        target = home / '.hermes/profiles' / args[1] / '.env'
        with target.open('a') as f: f.write('HERMES_DASHBOARD_BASIC_AUTH_PASSWORD=' + args[-1] + '\n')
'''

class Installers(unittest.TestCase):
    def test_profile_contains_safe_agent_starter(self):
        soul = (ROOT / 'profiles/starter-agent/SOUL.md').read_text()
        self.assertTrue(soul.startswith('# SOUL.md - Safe Agent Starter\n'))
        self.assertIn('[YOUR NAME]', soul)
        self.assertIn('## Approval gates', soul)
        self.assertIn('## Secrets and sensitive systems', soul)
        self.assertIn('## Verification and recovery', soul)

    def test_profile_template_is_bundled(self):
        for path, expected in sync.template_scripts().items():
            self.assertEqual(path.read_text(), expected)
            self.assertNotIn('raw.githubusercontent.com/benczb', expected)

    @unittest.skipIf(os.name == 'nt', 'POSIX shell execution; Windows AST checked separately')
    def test_mock_install_rerun_and_failure_paths(self):
        for platform in ('Linux', 'Darwin'):
            for failure in ('', 'docker', 'auth', 'custom-home', 'fresh-install', 'occupied-port', 'explicit-busy', 'skip-profile', 'custom-profile', 'explicit-profile', 'local-terminal', 'official-reuse', 'custom-port'):
                with self.subTest(platform=platform, failure=failure), tempfile.TemporaryDirectory() as tmp:
                    fixture = Path(tmp)
                    # Child-process fixture home only; never touches the real user's home.
                    user_home = fixture / 'user home'
                    user_home.mkdir()
                    bin_dir = fixture / 'bin'
                    bin_dir.mkdir()
                    for name in ('id', 'uname', 'docker', 'tailscale', 'sudo', 'curl', 'openssl', 'hermes', 'brew', 'xcode-select', 'open', 'launchctl', 'systemctl', 'apt-get', 'sleep'):
                        p = bin_dir / name
                        p.write_text(MOCK)
                        p.chmod(0o755)
                    hermes_source = fixture / 'mock-hermes-source'
                    hermes_source.write_text(MOCK)
                    if failure == 'fresh-install':
                        (bin_dir / 'hermes').unlink()
                    if failure == 'official-reuse':
                        (bin_dir / 'brew').unlink()
                    log = fixture / 'calls.jsonl'
                    env = dict(os.environ, HOME=str(user_home), PATH=str(bin_dir) + os.pathsep + os.environ['PATH'], MOCK_LOG=str(log), MOCK_OS=platform, MOCK_FAIL='' if failure in ('custom-home', 'fresh-install') else failure, MOCK_HERMES_SOURCE=str(hermes_source), MOCK_BIN=str(bin_dir))
                    custom_home = fixture / 'existing custom hermes'
                    custom_home.mkdir()
                    sentinel = custom_home / 'keep.txt'
                    sentinel.write_text('existing data')
                    env.pop('HERMES_HOME', None)
                    if failure == 'custom-home':
                        env['HERMES_HOME'] = str(custom_home)
                    env.pop('HERMES_PROFILE_SOURCE', None)
                    env.pop('HERMES_PROFILE_NAME', None)
                    env.pop('HERMES_INSTALLER_BASE_URL', None)
                    env.pop('HERMES_RESET_DASHBOARD_AUTH', None)
                    env.pop('HERMES_BACKEND_PORT', None)
                    env.pop('HERMES_SKIP_PROFILE_SETUP', None)
                    env.pop('HERMES_TERMINAL_BACKEND', None)
                    env.pop('HERMES_USE_EXISTING_DESKTOP', None)
                    env.pop('HERMES_TAILNET_PORT', None)
                    access_port = '9234' if failure == 'custom-port' else '9119'
                    if failure == 'custom-port': env['HERMES_TAILNET_PORT'] = access_port
                    if failure == 'official-reuse': env['HERMES_USE_EXISTING_DESKTOP'] = '1'
                    terminal_backend = 'local' if failure == 'local-terminal' else 'docker'
                    if failure == 'local-terminal':
                        env['HERMES_TERMINAL_BACKEND'] = 'local'
                        env['MOCK_FAIL'] = 'docker'
                    if failure == 'skip-profile':
                        env['HERMES_SKIP_PROFILE_SETUP'] = '1'
                    if failure == 'explicit-busy':
                        env['HERMES_BACKEND_PORT'] = '9119'
                    selected_profile = 'Hamburger_01' if failure == 'custom-profile' else ('personal' if failure == 'explicit-profile' else 'starter-agent')
                    if failure == 'explicit-profile':
                        env['HERMES_PROFILE_NAME'] = selected_profile
                    chosen_password = "Fixture $ # ' \\ password!"
                    # Blank username, short password and confirmation mismatch must reprompt.
                    visibility = 'y' if failure == 'custom-home' else ''
                    answers = '\nben-workshop\n' + visibility + '\nshort\n' + chosen_password + '\nmismatch\n' + chosen_password + '\n' + chosen_password + '\n'
                    profile_answers = 'bad/name\nCON\nDefault\n' + selected_profile + '\n' if failure == 'custom-profile' else ('' if failure == 'explicit-profile' else '\n')
                    answers = profile_answers + answers
                    result = subprocess.run(['/bin/bash', str(ROOT / 'scripts/setup-macos-linux.sh')], env=env, input=answers, capture_output=True, text=True, timeout=30)
                    calls = [json.loads(line) for line in log.read_text().splitlines()]
                    if platform == 'Darwin' and failure != 'official-reuse':
                        self.assertIn(['brew', 'install', 'openssl@3', 'pkg-config'], calls)
                        self.assertIn(['brew', '--prefix', 'openssl@3'], calls)
                    local_port = '9120' if failure == 'occupied-port' else access_port
                    forward = ['tailscale', 'serve', '--bg', '--tcp=' + access_port, 'tcp://127.0.0.1:' + local_port]
                    if failure in ('docker', 'auth', 'explicit-busy'):
                        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                        self.assertNotIn(forward, calls)
                        continue
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertIn(forward, calls)
                    if failure == 'local-terminal':
                        self.assertFalse(any(c[0] == 'docker' or c == ['open', '-a', 'Docker'] or (c[0] == 'brew' and 'docker' in c) or (c[0] == 'apt-get' and 'docker.io' in c) for c in calls))
                        self.assertIn('Docker: not required (local terminal)', (user_home / '.hermes-workshop-installer' / selected_profile / 'installation-ready.txt').read_text())
                    wizard = ['hermes', '-p', selected_profile, 'setup']
                    if failure == 'skip-profile':
                        self.assertNotIn(wizard, calls)
                    else:
                        self.assertGreater(calls.index(wizard), calls.index(forward))
                        if failure != 'official-reuse':
                            self.assertGreater(calls.index(wizard), calls.index(['hermes', '-p', selected_profile, 'desktop', '--build-only']))
                    if failure == 'official-reuse':
                        self.assertFalse(any(c[0] == 'brew' or any('Homebrew/install' in arg for arg in c) for c in calls))
                        self.assertNotIn(['hermes', '-p', selected_profile, 'desktop', '--build-only'], calls)
                        self.assertFalse(any(c[0] == 'curl' and any('hermes-agent/' in arg and arg.endswith('/scripts/install.sh') for arg in c) for c in calls))
                    ready_state = user_home / '.hermes-workshop-installer' / selected_profile / 'installation-ready.txt'
                    self.assertIn('INSTALLATION CHECKS COMPLETE', ready_state.read_text())

                    self.assertIn(['hermes', '-p', selected_profile, 'config', 'set', 'terminal.backend', terminal_backend], calls)
                    expected_cwd = str(user_home / '.hermes/profiles' / selected_profile / 'workspace') if terminal_backend == 'local' else '/workspace'
                    self.assertIn(['hermes', '-p', selected_profile, 'config', 'set', 'terminal.cwd', expected_cwd], calls)
                    if terminal_backend == 'local':
                        self.assertTrue(Path(expected_cwd).is_dir())
                    self.assertIn(['hermes', '-p', selected_profile, 'config', 'set', 'dashboard.public_url', 'http://100.80.90.10:' + access_port], calls)
                    credentials = user_home / '.hermes-workshop-installer' / selected_profile / 'dashboard-login.txt'
                    if failure == 'fresh-install':
                        self.assertTrue((user_home / '.hermes').is_dir())
                        self.assertTrue(any(c[0] == 'curl' and any('hermes-agent/' in arg and arg.endswith('/scripts/install.sh') for arg in c) for c in calls))
                    self.assertIn(['hermes', '-p', selected_profile, 'config', 'set', 'HERMES_DASHBOARD_BASIC_AUTH_USERNAME', 'ben-workshop'], calls)
                    self.assertIn(['hermes', '-p', selected_profile, 'config', 'set', 'HERMES_DASHBOARD_BASIC_AUTH_PASSWORD', chosen_password], calls)
                    self.assertNotIn(chosen_password, result.stdout + result.stderr)
                    old_credentials = credentials.read_text()
                    self.assertIn('Username: ben-workshop', old_credentials)
                    self.assertEqual(credentials.stat().st_mode & 0o777, 0o600)
                    custom_soul = user_home / '.hermes/profiles' / selected_profile / 'SOUL.md'
                    custom_soul.write_text('Keep the user customization.')
                    result = subprocess.run(['/bin/bash', str(ROOT / 'scripts/setup-macos-linux.sh')], env=env, input='' if failure == 'explicit-profile' else '\n', capture_output=True, text=True, timeout=30)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    rerun_calls = [json.loads(line) for line in log.read_text().splitlines()]
                    if failure == 'local-terminal':
                        self.assertFalse(any(c[0] == 'docker' for c in rerun_calls))
                        self.assertFalse(any(c[-2:] == ['terminal.backend', 'docker'] for c in rerun_calls))
                    self.assertEqual(credentials.read_text(), old_credentials)
                    self.assertEqual(custom_soul.read_text(), 'Keep the user customization.')
                    self.assertEqual((user_home / '.hermes-workshop-installer/_bootstrap/last-profile').read_text().strip(), selected_profile)
                    if failure in ('custom-profile', 'explicit-profile'):
                        self.assertFalse((user_home / '.hermes/profiles/starter-agent').exists())
                    if platform == 'Linux' and failure == '':
                        reset_env = dict(env, HERMES_RESET_DASHBOARD_AUTH='1')
                        reset_answers = '\nnew-user\ny\n' + chosen_password + '\n' + chosen_password + '\n'
                        reset = subprocess.run(['/bin/bash', str(ROOT / 'scripts/setup-macos-linux.sh')], env=reset_env, input=reset_answers, capture_output=True, text=True, timeout=30)
                        self.assertEqual(reset.returncode, 0, reset.stdout + reset.stderr)
                        self.assertIn('Username: new-user', credentials.read_text())

                    calls = [json.loads(line) for line in log.read_text().splitlines()]
                    self.assertEqual(sum(c[:3] == ['hermes', 'profile', 'install'] for c in calls), 1)
                    backend = user_home / '.hermes-workshop-installer' / selected_profile / 'backend.sh'
                    subprocess.run(['/bin/bash', '-n', str(backend)], check=True)
                    self.assertIn('serve --isolated --host 127.0.0.1 --port ' + local_port, backend.read_text())
                    self.assertEqual((backend.parent / 'backend-port').read_text().strip(), local_port)
                    self.assertFalse(any(c[0] in ('kill', 'pkill') for c in calls))
                    # Login services can inherit HERMES_HOME independently of the installer.
                    backend_env = dict(env, HERMES_HOME=str(custom_home))
                    probe = subprocess.run(['/bin/bash', str(backend)], env=backend_env, capture_output=True, text=True, timeout=10)
                    self.assertEqual(probe.returncode, 0, probe.stdout + probe.stderr)
                    self.assertEqual(sentinel.read_text(), 'existing data')
                    self.assertFalse((custom_home / 'profiles').exists())
                    if platform == 'Darwin':
                        import plistlib
                        plist = user_home / 'Library/LaunchAgents' / ('com.hermes.workshop.' + selected_profile + '.plist')
                        self.assertEqual(plistlib.loads(plist.read_bytes())['ProgramArguments'][1], str(backend))

if __name__ == '__main__':
    unittest.main(verbosity=2)
