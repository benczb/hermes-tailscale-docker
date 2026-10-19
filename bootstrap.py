#!/usr/bin/env python3
"""SID workshop bootstrap (native runtime). Python standard library only.

Architectural model (the "terminal in Docker" inversion):

* The Hermes runtime itself is installed NATIVELY on the host with the official
  one-liner (install.sh / install.ps1). Native installs update with ``hermes update``
  or the Desktop app's one-click update -- no terminal is required for future updates.
* Docker Desktop is retained, but ONLY as the Hermes **terminal sandbox backend**
  (``terminal.backend: docker``). The agent's shell commands and file tools run inside
  a disposable sandbox container; the runtime, the dashboard and the Desktop GUI do not.
* A fresh, synthetic-data-only Hermes data home is seeded from an explicit allowlist
  (never anyone's live profile) and carries the training config: the Docker terminal
  backend, scoped training-data volumes (no broad host mounts, no credentials) and the
  authenticated dashboard on loopback 9119.
* The dashboard health check proves the authenticated cookie gate engages before any
  host Tailscale Serve TCP rule is added (that rule is added only after a second,
  explicit consent).

No live host package installs, service restarts or remote Docker contexts are performed
by the tests; the orchestrator stages are consent-gated and mockable.
"""
import argparse
import getpass
import hashlib
import http.cookiejar
import json
import os
from pathlib import Path
import platform
import secrets
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parent
PORT = 9119
BASE = 'http://127.0.0.1:9119'
INSTALL_SH = 'https://hermes-agent.nousresearch.com/install.sh'
INSTALL_PS1 = 'https://hermes-agent.nousresearch.com/install.ps1'
# Synthetic training material only. No working profile, credentials, sessions,
# memory, real board documents, cron jobs, MCP servers or plugins are seeded.
ALLOWLIST = ('SOUL.md', 'skills/sid-board-review/SKILL.md', 'training/risk-register.csv',
             'training/board-paper.txt', 'training/exercises.md')


def run(*args, capture=False, env=None, check=True):
    return subprocess.run(args, check=check, text=True, env=env,
                          stdout=subprocess.PIPE if capture else None)


def consent(message):
    if input(message + ' [yes/NO]: ').strip().lower() != 'yes':
        raise RuntimeError('Declined. No further changes made.')


def pins():
    return json.loads((ROOT / 'versions.json').read_text(encoding='utf-8'))


def native_install_command():
    """The official one-liner for this host. Native installs update via
    ``hermes update`` or the Desktop GUI -- no terminal needed for future updates."""
    if platform.system() == 'Windows':
        return 'iex (irm ' + INSTALL_PS1 + ')'
    return 'curl -fsSL ' + INSTALL_SH + ' | bash'


def docker_available():
    """Docker Desktop / Engine must be on PATH with a reachable local engine.
    Remote Docker contexts are rejected: the terminal sandbox must run on this host."""
    if not shutil.which('docker'):
        raise RuntimeError('docker is missing from PATH. Start Docker Desktop (or install the '
                           'Docker Engine) on the host first -- it is required only as the '
                           'terminal sandbox backend, see README prerequisites.')
    run('docker', 'info', capture=True)
    if os.environ.get('DOCKER_HOST') or os.environ.get('DOCKER_CONTEXT'):
        raise RuntimeError('Unset DOCKER_HOST/DOCKER_CONTEXT and select the local Docker context '
                           'first; the terminal sandbox must run on this host.')
    context = json.loads(run('docker', 'context', 'inspect', capture=True).stdout)
    endpoint = context[0].get('Endpoints', {}).get('docker', {}).get('Host', '')
    if not endpoint.startswith(('unix://', 'npipe://')):
        raise RuntimeError('Only a local Docker engine socket is supported for the terminal '
                           'sandbox, not SSH/TCP contexts.')


def preflight(target, check_docker=True, check_tailscale=True):
    if target.exists() or target.is_symlink():
        raise RuntimeError('Target already exists. Refusing to overwrite: ' + str(target))
    system = platform.system()
    if system not in ('Darwin', 'Linux', 'Windows'):
        raise RuntimeError('Unsupported host: ' + system)
    if system == 'Linux' and 'microsoft' in platform.release().lower():
        raise RuntimeError('Use native Windows PowerShell, not WSL: the host Tailscale must run on Windows.')
    if check_docker:
        docker_available()
    if check_tailscale:
        if not shutil.which('tailscale'):
            raise RuntimeError('tailscale is missing from PATH. See README prerequisites; '
                               'install it on the host and sign in first.')
        state = json.loads(run('tailscale', 'status', '--json', capture=True).stdout)
        if state.get('BackendState') != 'Running':
            raise RuntimeError('Sign in to host Tailscale and connect before continuing.')
        serve = json.loads(run('tailscale', 'serve', 'status', '--json', capture=True).stdout or '{}')
        if serve:
            raise RuntimeError('Existing Tailscale Serve configuration detected. Refusing to change it. '
                               'Ask your facilitator.')
        return state
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', PORT))
    return None


def training_config():
    """Minimal, reviewed training config: Docker terminal sandbox backend, scoped training
    data volume, no broad host mounts, credentials excluded."""
    return (
        '# SID training home -- generated by bootstrap.py. Keep credentials in .env, never here.\n'
        'terminal:\n'
        '  backend: docker\n'
        '  # Only the synthetic training data is mounted into the sandbox; the host home and\n'
        '  # Docker socket are NOT mounted, and no credentials are exposed to the container.\n'
        '  docker_volumes: ["/opt/sid-training:/opt/sid-training:ro"]\n'
    )


def seed(target, password):
    # Exclusive directory creation is also the concurrency/overwrite guard.
    target.mkdir(mode=0o700, parents=True, exist_ok=False)
    home = target / 'home'
    home.mkdir(mode=0o700)
    for rel in ALLOWLIST:
        source = ROOT / 'profile' / rel
        if source.is_symlink() or not source.is_file():
            raise RuntimeError('Invalid template file: ' + rel)
        dest = home / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open('xb') as handle:
            handle.write(source.read_bytes())
    (home / 'config.yaml').write_text(training_config(), encoding='utf-8')
    # A private, standalone data home (HERMES_HOME), not a clone/export of anyone's
    # working profile. The dashboard password and signing secret live in .env only.
    env_path = home / '.env'
    with env_path.open('x', encoding='utf-8') as handle:
        os.chmod(handle.name, 0o600)
        handle.write('# Dashboard authentication (basic provider). Never commit this file.\n'
                     'HERMES_DASHBOARD_BASIC_AUTH_USERNAME=participant\n'
                     'HERMES_DASHBOARD_BASIC_AUTH_PASSWORD=' + password + '\n'
                     'HERMES_DASHBOARD_BASIC_AUTH_SECRET=' + secrets.token_hex(32) + '\n')


def serve_env():
    """Environment for the native dashboard: loopback host/port, HERMES_HOME pointed at
    the seeded training home. Loopback serving needs no --insecure; the cookie gate
    still engages because the basic auth provider is configured in .env."""
    env = os.environ.copy()
    env['HERMES_HOME'] = str(_active_home)
    env['HERMES_DASHBOARD_HOST'] = '127.0.0.1'
    env['HERMES_DASHBOARD_PORT'] = str(PORT)
    return env


_active_home = None


def request(opener, path, body=None):
    payload = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=payload,
                                 headers={'Content-Type': 'application/json'})
    try:
        with opener.open(req, timeout=10) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as exc:
        code = exc.code
        exc.close()
        return code, None


def health(password, attempts=30):
    # HTTP Basic (-u) does not authenticate this release. Use its password form
    # endpoint and cookie session, then prove the protected API rejects strangers.
    for attempt in range(attempts):
        try:
            anonymous = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
            code, _ = request(anonymous, '/api/status')
            if code not in (401, 403):
                raise RuntimeError('Protected API did not reject anonymous access (HTTP ' + str(code) + ').')
            code, _ = request(anonymous, '/auth/password-login',
                              {'provider': 'basic', 'username': 'participant', 'password': secrets.token_hex(24)})
            if code != 401:
                raise RuntimeError('Incorrect password was not rejected.')
            authenticated = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
            code, body = request(authenticated, '/auth/password-login',
                                 {'provider': 'basic', 'username': 'participant', 'password': password})
            if code != 200 or not body or body.get('ok') is not True:
                raise RuntimeError('Dashboard password sign-in failed.')
            code, body = request(authenticated, '/api/status')
            if code != 200 or not isinstance(body, dict):
                raise RuntimeError('Authenticated status probe failed.')
            return
        except (urllib.error.URLError, TimeoutError, ConnectionError, json.JSONDecodeError):
            if attempt + 1 == attempts:
                raise RuntimeError('Dashboard did not become ready. Inspect the native dashboard logs locally.')
            time.sleep(2)


def download(artifact, destination):
    if destination.exists():
        raise RuntimeError('Download already exists: ' + str(destination))
    digest = hashlib.sha256()
    partial = destination.with_suffix(destination.suffix + '.partial')
    if partial.exists() or partial.is_symlink():
        raise RuntimeError('Partial download already exists; inspect it first: ' + str(partial))
    try:
        with urllib.request.urlopen(artifact['url'], timeout=60) as source, partial.open('xb') as output:
            while True:
                block = source.read(1024 * 1024)
                if not block:
                    break
                output.write(block)
                digest.update(block)
        if digest.hexdigest() != artifact['sha256']:
            raise RuntimeError('Download checksum mismatch. Nothing will be opened.')
        partial.rename(destination)
    finally:
        if partial.exists():
            partial.unlink()


def desktop():
    system = platform.system()
    key = 'macos-arm64' if system == 'Darwin' and platform.machine().lower() in ('arm64', 'aarch64') else 'windows' if system == 'Windows' else None
    if not key:
        print('No pinned first-party binary for this platform in the verified stable receipt.\n'
              'Linux: follow the official Desktop/source guide (it builds from the same source).\n'
              'https://hermes-agent.nousresearch.com/docs/user-guide/desktop\n'
              'The native runtime is independent and updates with `hermes update`. No community app is substituted.')
        return
    artifact = pins()['desktop'][key]
    print('Official Desktop ' + pins()['desktop']['version'] + ': ' + artifact['url'])
    print('Large download (1.6 GB macOS / 4.3 GB Windows). Existing Desktop installations are not modified automatically.')
    consent('Download a checksum-verified Desktop package to your Downloads folder?')
    folder = Path.home() / 'Downloads'
    if not folder.is_dir():
        raise RuntimeError('Create your Downloads folder first.')
    dest = folder / artifact['url'].rsplit('/', 1)[1]
    download(artifact, dest)
    print('Verified package: ' + str(dest))
    consent('Open the package? You control extraction/installation and must avoid replacing an existing app without approval')
    if system == 'Darwin':
        run('open', str(dest))
    else:
        os.startfile(str(dest))
    print('Finish the OS installation. The Desktop drives the same native backend -- sign in with '
          'the dashboard username `participant` and your password. It checks for updates in the '
          'background and offers a one-click update (no terminal needed).')


def main():
    global _active_home
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--home', type=Path, default=Path.home() / 'hermes-sid-training',
                        help='fresh, synthetic-data-only Hermes data home (HERMES_HOME)')
    parser.add_argument('--directory', type=Path, default=None, help='alias for --home (kept for the slides)')
    parser.add_argument('--desktop', action='store_true', help='guided official host Desktop package download only')
    args = parser.parse_args()
    if args.desktop:
        desktop()
        return
    target = (args.directory or args.home).expanduser().absolute()
    _active_home = target / 'home'
    print('SID training: NATIVE Hermes runtime + Docker terminal sandbox.\n'
          'New data home (HERMES_HOME) at ' + str(_active_home) + '\n'
          'Prerequisites (host, consented): Python 3.9+, Docker Desktop/Engine running, Tailscale signed in.\n'
          'This stage does not install host packages or touch your real ~/.hermes. '
          'Docker runs sandboxed agent commands; models may transmit prompts and incur charges. '
          'Use synthetic data only.')
    state = preflight(target)
    consent('Seed the NEW training home and run the official native Hermes installer for it '
            '(this clones/builds Hermes under that home -- not your real ~/.hermes)?')
    password = getpass.getpass('Choose a dashboard password (at least 16 characters; not a model API key): ')
    if len(password) < 16 or password != password.strip() or any(c in password for c in '\r\n\x00'):
        raise RuntimeError('Password needs 16+ characters, no surrounding whitespace, newlines or NUL.')
    if getpass.getpass('Confirm password: ') != password:
        raise RuntimeError('Passwords do not match.')
    seed(target, password)
    print('Private .env contains a plaintext dashboard password and secret. Never share the home folder.\n'
          'On Windows: review NTFS permissions; only your account and administrators should have access.')
    # Native install, scoped to the training home, so the real ~/.hermes is untouched.
    env = serve_env()
    print('Installing native Hermes (official installer) into ' + str(_active_home) + ' ...')
    if platform.system() == 'Windows':
        run('powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command',
            'iex (irm ' + INSTALL_PS1 + ')', env=env)
    else:
        run('bash', '-c', 'curl -fsSL ' + INSTALL_SH + ' | bash', env=env)
    # The dashboard binds loopback 127.0.0.1:9119 by default; the cookie gate engages
    # because the basic auth provider is configured in .env. No --insecure, no 0.0.0.0.
    run('hermes', 'dashboard', '--host', '127.0.0.1', '--port', str(PORT), env=env)
    health(password)
    print('Local authentication verified: anonymous and wrong-password requests denied, signed-in status OK.')
    if state is None:
        print('Tailnet access was skipped (Tailscale not checked). The dashboard stays loopback-only.\n'
              'To share it privately later, sign in to Tailscale and rerun, or run the serve rule yourself.')
        return
    consent('Expose port 9119 to your tailnet using Tailscale Serve? Tailnet ACLs must restrict access; this is NOT Funnel')
    # Recheck just before mutation so another session's newly added config is not replaced.
    existing = json.loads(run('tailscale', 'serve', 'status', '--json', capture=True).stdout or '{}')
    if existing:
        raise RuntimeError('Serve configuration changed during setup. Not touching it.')
    run('tailscale', 'serve', '--bg', '--tcp=9119', 'tcp://127.0.0.1:9119')
    serving = json.loads(run('tailscale', 'serve', 'status', '--json', capture=True).stdout)
    rule = serving.get('TCP', {}).get('9119', {})
    if rule.get('TCPForward') != '127.0.0.1:9119':
        raise RuntimeError('Serve read-back does not confirm the expected TCP forwarding rule. Check tailscale serve status.')
    dns = state.get('Self', {}).get('DNSName', '').rstrip('.')
    print('Native runtime ready: ' + BASE + '\nTailnet address: ' + ('http://' + dns + ':9119' if dns else 'see tailscale status'))
    print('Tailnet TCP transport is encrypted by Tailscale; this is not browser HTTPS.\n'
          'Future updates: `hermes update` in a terminal OR the one-click update inside Desktop -- no terminal required.\n'
          'Agent commands run in the Docker terminal sandbox (Docker Desktop). Run the synthetic '
          'exercises in training/exercises.md. No model response has been tested by this installer.')


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, OSError, ValueError, subprocess.CalledProcessError, KeyboardInterrupt) as exc:
        print('STOPPED: ' + str(exc) + '\nAny newly created training data is preserved. See README for recovery.', file=sys.stderr)
        sys.exit(1)
