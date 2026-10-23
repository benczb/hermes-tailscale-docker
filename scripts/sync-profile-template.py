#!/usr/bin/env python3
"""Embed the authored workshop profile into the standalone installers."""
import argparse
from pathlib import Path
import re
ROOT = Path(__file__).resolve().parents[1]

def template_scripts():
    files = ['distribution.yaml', 'config.yaml', 'SOUL.md']
    bash_lines = []
    for name in files:
        content = (ROOT / 'profiles/workshop' / name).read_text()
        bash_lines.append(f'    cat > "$state/template/{name}" <<\'WORKSHOP_FILE\'\n' + content.rstrip('\n') + '\nWORKSHOP_FILE')
    result = {}
    for filename, block in [('setup-macos-linux.sh', '\n'.join(bash_lines))]:
        path = ROOT / 'scripts' / filename
        content = path.read_text()
        pattern = r'(?m)^([ ]*)# BEGIN WORKSHOP TEMPLATE\n.*?^[ ]*# END WORKSHOP TEMPLATE'
        content, count = re.subn(pattern, lambda m: m[1] + '# BEGIN WORKSHOP TEMPLATE\n' + block + '\n' + m[1] + '# END WORKSHOP TEMPLATE', content, flags=re.S)
        if count != 1:
            raise ValueError(f'Expected template markers in {filename}')
        result[path] = content
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    for path, content in template_scripts().items():
        if args.check:
            if path.read_text() != content:
                raise SystemExit(f'{path.name} template is stale; run scripts/sync-profile-template.py')
        else:
            path.write_text(content)
