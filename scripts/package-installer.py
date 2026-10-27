#!/usr/bin/env python3
"""Build deterministic public per-OS ZIPs, preserving executable launchers."""
import argparse
import hashlib
import io
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
COMMON = ['README.md', 'LICENSE', 'AGENTS.md', 'CONTRIBUTING.md', 'CODE_OF_CONDUCT.md',
          'SECURITY.md', 'SUPPORT.md', 'CHANGELOG.md', 'docs/command-setup.md',
          'docs/agent-install.md', 'docs/releasing.md', 'docs/installer-audit.md', 'profiles/starter-agent/.gitignore',
          'profiles/starter-agent/distribution.yaml', 'profiles/starter-agent/config.yaml', 'profiles/starter-agent/SOUL.md']
PLATFORMS = {
    'macos': ['Install-Hermes.command', 'scripts/setup-macos-linux.sh'],
    'linux': ['Install-Hermes.sh', 'scripts/setup-macos-linux.sh'],
    'windows': ['Install-Hermes.cmd', 'scripts/setup-windows.ps1', 'scripts/launch-windows.ps1'],
}

def zip_bytes(files):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name in files:
            info = zipfile.ZipInfo('hermes-starter-agent-installer/' + name)
            info.create_system = 3
            mode = 0o100755 if name.endswith(('.sh', '.command')) else 0o100644
            info.external_attr = mode << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, (ROOT / name).read_bytes())
    data = buffer.getvalue()
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        assert archive.testzip() is None
        for name in files:
            if name.endswith(('.sh', '.command')):
                assert archive.getinfo('hermes-starter-agent-installer/' + name).external_attr >> 16 & 0o111
    return data

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true', help='Fail if committed public downloads are stale')
    args = parser.parse_args()
    checksums = []
    for platform, files in PLATFORMS.items():
        path = ROOT / 'downloads' / f'hermes-workshop-{platform}.zip'
        data = zip_bytes(COMMON + files)
        if args.check:
            if not path.exists() or path.read_bytes() != data:
                raise SystemExit(f'{path.name} is stale; run python scripts/package-installer.py')
        else:
            path.parent.mkdir(exist_ok=True)
            path.write_bytes(data)
        checksums.append(hashlib.sha256(data).hexdigest() + '  ' + path.name)
        print(f'{platform}: {len(data)} bytes')
    sums = ROOT / 'downloads/SHA256SUMS'
    expected = '\n'.join(checksums) + '\n'
    if args.check:
        if not sums.exists() or sums.read_text() != expected:
            raise SystemExit('Public download checksums are stale')
    else:
        sums.write_text(expected)
    # Retain a combined CI artifact for maintainers.
    all_files = COMMON + list(dict.fromkeys(file for files in PLATFORMS.values() for file in files))
    output = ROOT / 'work/hermes-workshop-installer.zip'
    output.parent.mkdir(exist_ok=True)
    output.write_bytes(zip_bytes(all_files))
