#!/usr/bin/env python3
"""SID workshop bootstrap. Python standard library only."""
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
import webbrowser

ROOT = Path(__file__).resolve().parent
PORT = 9119
BASE = 'http://127.0.0.1:9119'
ALLOWLIST = ('SOUL.md', 'skills/sid-board-review/SKILL.md', 'training/risk-register.csv',
             'training/board-paper.txt', 'training/exercises.md')


def run(*args, capture=False):
    return subprocess.run(args, check=True, text=True,
                          stdout=subprocess.PIPE if capture else None)


def consent(message):
    if input(message + ' [yes/NO]: ').strip().lower() != 'yes':
        raise RuntimeError('Declined. No further changes made.')


def pins():
    return json.loads((ROOT / 'versions.json').read_text(encoding='utf-8'))


def preflight(target):
    if target.exists() or target.is_symlink():
        raise RuntimeError('Target already exists. Refusing to overwrite: ' + str(target))
    system = platform.system()
    if system not in ('Darwin', 'Linux', 'Windows'):
        raise RuntimeError('Unsupported host: ' + system)
    if system == 'Linux' and 'microsoft' in platform.release().lower():
        raise RuntimeError('Use native Windows PowerShell, not WSL: Tailscale must run on the host.')
    for name in ('docker', 'tailscale'):
        if not shutil.which(name):
            raise RuntimeError(name + ' is missing from PATH. See README prerequisites; install it on the host first.')
    run('docker', 'compose', 'version', capture=True)
    if os.environ.get('DOCKER_HOST') or os.environ.get('DOCKER_CONTEXT'):
        raise RuntimeError('Unset DOCKER_HOST/DOCKER_CONTEXT and select a local Docker context first.')
    context = json.loads(run('docker', 'context', 'inspect', capture=True).stdout)
    endpoint = context[0].get('Endpoints', {}).get('docker', {}).get('Host', '')
    if not endpoint.startswith(('unix://', 'npipe://')):
        raise RuntimeError('Only a local Docker engine socket is supported, not SSH/TCP contexts.')
    run('docker', 'info', capture=True)
    projects = json.loads(run('docker', 'compose', 'ls', '--all', '--format', 'json', capture=True).stdout)
    if any(item.get('Name') == 'sid-training' for item in projects):
        raise RuntimeError('A sid-training Compose project already exists. Refusing to replace it.')
    state = json.loads(run('tailscale', 'status', '--json', capture=True).stdout)
    if state.get('BackendState') != 'Running':
        raise RuntimeError('Sign in to host Tailscale and connect before continuing.')
    serve = json.loads(run('tailscale', 'serve', 'status', '--json', capture=True).stdout or '{}')
    if serve:
        raise RuntimeError('Existing Tailscale Serve configuration detected. Refusing to change it. Ask your facilitator.')
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', PORT))
    return state


def compose_text(image):
    return '''name: sid-training
services:
  hermes:
    image: IMAGE
    restart: unless-stopped
    ports:
      - "127.0.0.1:9119:9119"
    volumes:
      - "./data:/opt/data"
    env_file:
      - path: ./runtime.env
        format: raw
    environment:
      HERMES_DASHBOARD: "1"
      HERMES_DASHBOARD_HOST: "0.0.0.0"
      HERMES_DASHBOARD_PORT: "9119"
    command: ["gateway", "run"]
'''.replace('IMAGE', image)


def seed(target, password):
    # Exclusive directory creation is also the concurrency/overwrite guard.
    target.mkdir(mode=0o700, parents=True, exist_ok=False)
    data = target / 'data'
    data.mkdir(mode=0o700)
    for rel in ALLOWLIST:
        source = ROOT / 'profile' / rel
        if source.is_symlink() or not source.is_file():
            raise RuntimeError('Invalid template file: ' + rel)
        dest = data / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open('xb') as handle:
            handle.write(source.read_bytes())
    # A standalone data home, not a clone/export of anyone's working profile.
    (target / 'compose.yaml').write_text(compose_text(pins()['runtime']['image']), encoding='utf-8')
    with (target / 'runtime.env').open('x', encoding='utf-8') as handle:
        os.chmod(handle.name, 0o600)
        handle.write('HERMES_DASHBOARD_BASIC_AUTH_USERNAME=participant\n'
                     'HERMES_DASHBOARD_BASIC_AUTH_PASSWORD=' + password + '\n'
                     'HERMES_DASHBOARD_BASIC_AUTH_SECRET=' + secrets.token_hex(32) + '\n')


def compose(target, *args, capture=False):
    return run('docker', 'compose', '--project-directory', str(target),
               '-f', str(target / 'compose.yaml'), *args, capture=capture)


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
                raise RuntimeError('Dashboard did not become ready. Inspect docker compose logs locally.')
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
              'Linux: follow the official source/desktop guide. Intel macOS is unsupported.\n'
              'https://hermes-agent.nousresearch.com/docs/user-guide/desktop\n'
              'Runtime setup remains available independently. No community app is substituted.')
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
    print('Finish the OS installation. In Desktop use Settings > Gateways to add http://127.0.0.1:9119.\n'
          'Do not point it at the unrelated 8642 community-app API. Native sign-in uses the dashboard password.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=Path.home() / 'hermes-sid-training')
    parser.add_argument('--desktop', action='store_true', help='guided official host Desktop package download only')
    args = parser.parse_args()
    if args.desktop:
        desktop()
        return
    target = args.directory.expanduser().absolute()
    print('SID training: new standalone Docker data home at ' + str(target))
    print('Prerequisites: host Docker with Compose >=2.30, signed-in host Tailscale and Python >=3.9.\n'
          'No package installation, daemon start, shell configuration edit or existing-profile import is performed.\n'
          'Docker can execute code on this host. Models may transmit prompts and incur charges. Use synthetic data only.')
    state = preflight(target)
    # Require raw env_file support rather than silently interpolating user secrets.
    version = run('docker', 'compose', 'version', '--short', capture=True).stdout.strip().lstrip('v')
    import re
    match = re.match(r'(\d+)\.(\d+)', version)
    if not match or tuple(map(int, match.groups())) < (2, 30):
        raise RuntimeError('Docker Compose >=2.30 is required for raw secrets env files.')
    consent('Create this NEW training home, pull the pinned image, run provider setup and start its container?')
    password = getpass.getpass('Choose a dashboard password (at least 16 characters; not a model API key): ')
    if len(password) < 16 or password != password.strip() or any(c in password for c in '\r\n\x00'):
        raise RuntimeError('Password needs 16+ characters, no surrounding whitespace, newlines or NUL.')
    if getpass.getpass('Confirm password: ') != password:
        raise RuntimeError('Passwords do not match.')
    seed(target, password)
    print('Private runtime.env contains a plaintext dashboard password. Never share the installation folder.\n'
          'On Windows: review NTFS permissions; only your account and administrators should have access.')
    compose(target, 'config', '--quiet')
    compose(target, 'pull', 'hermes')
    compose(target, 'run', '--rm', 'hermes', 'setup')
    compose(target, 'up', '-d', 'hermes')
    health(password)
    print('Local authentication verified: anonymous and wrong-password requests denied, signed-in status OK.')
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
    print('Runtime ready: ' + BASE + '\nTailnet address: ' + ('http://' + dns + ':9119' if dns else 'see tailscale status'))
    print('Tailnet TCP transport is encrypted by Tailscale; this is not browser HTTPS.\n'
          'Next: run this bootstrap again with --desktop, then connect Desktop via Settings > Gateways.\n'
          'Run the synthetic exercises in data/training/exercises.md. No model response has been tested by this installer.')


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, OSError, ValueError, subprocess.CalledProcessError, KeyboardInterrupt) as exc:
        print('STOPPED: ' + str(exc) + '\nAny newly created training data is preserved. See README for recovery.', file=sys.stderr)
        sys.exit(1)
