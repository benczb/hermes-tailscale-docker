"""Launcher boundary tests; no component installation, npm or GUI is executed."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
REVISION = 'bd1260ac4249763a447db56faca582e4f5ade10c'
DIGEST = 'ceaec5f06ef08f7a78bb956d455aa51e3bae1b8285fc651181f26936e86a77a9'


class CommandLauncherTests(unittest.TestCase):
    def test_both_launchers_pin_same_source_and_hash(self):
        for name in ('start-setup.sh', 'start-setup.ps1'):
            text = (ROOT / name).read_text()
            self.assertIn(REVISION, text)
            self.assertIn(DIGEST, text)
            self.assertIn('npm', text)
            self.assertIn('ci --include=dev', text)
            self.assertNotIn('bootstrap.py', text)
            self.assertNotIn('Invoke-Expression', text)

    @unittest.skipIf(os.name == 'nt', 'Bash fixture runs on POSIX CI')
    def test_bash_checksum_failure_never_extracts_or_runs_dependencies(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            bins = work / 'bin'
            bins.mkdir()
            calls = work / 'calls'
            mocks = {
                'id': 'echo 1000',
                'uname': 'if [ "$1" = -s ]; then echo Darwin; else echo x86_64; fi',
                'node': 'exit 0',
                'curl': 'while [ "$#" -gt 0 ]; do if [ "$1" = -o ]; then shift; printf corrupt > "$1"; exit 0; fi; shift; done; exit 1',
                'unzip': 'echo unzip >> "$CALLS"',
                'npm': 'echo npm >> "$CALLS"',
            }
            for name, body in mocks.items():
                path = bins / name
                path.write_text('#!/bin/sh\n' + body + '\n')
                path.chmod(0o755)
            env = dict(os.environ, PATH=str(bins) + os.pathsep + os.environ['PATH'],
                       TMPDIR=tmp, CALLS=str(calls))
            result = subprocess.run(['bash', str(ROOT / 'start-setup.sh')],
                                    env=env, text=True, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('checksum mismatch', result.stderr)
            self.assertFalse(calls.exists(), result.stdout + result.stderr)
            self.assertFalse(list(work.glob('hermes-companion.*/source.zip')))

    @unittest.skipIf(os.name == 'nt', 'Bash fixture runs on POSIX CI')
    def test_bash_verified_snapshot_opens_gui_from_expected_directory(self):
        # SHA tool is stubbed only for this control-flow fixture; actual archive
        # digest is also checked separately when the real archive is available.
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            bins = work / 'bin'
            bins.mkdir()
            calls = work / 'calls'
            mocks = {
                'id': 'echo 1000',
                'uname': 'if [ "$1" = -s ]; then echo Darwin; else echo x86_64; fi',
                'node': 'exit 0',
                'curl': 'while [ "$#" -gt 0 ]; do if [ "$1" = -o ]; then shift; printf fixture > "$1"; exit 0; fi; shift; done; exit 1',
                'shasum': f'echo "{DIGEST}  fixture"',
                'unzip': f'while [ "$#" -gt 0 ]; do if [ "$1" = -d ]; then shift; mkdir -p "$1/hermes-tailscale-docker-{REVISION}/installer-ui"; exit 0; fi; shift; done; exit 1',
                'npm': 'printf "%s|%s\\n" "$PWD" "$*" >> "$CALLS"',
            }
            for name, body in mocks.items():
                path = bins / name
                path.write_text('#!/bin/sh\n' + body + '\n')
                path.chmod(0o755)
            env = dict(os.environ, PATH=str(bins) + os.pathsep + os.environ['PATH'],
                       TMPDIR=tmp, CALLS=str(calls))
            result = subprocess.run(['bash', str(ROOT / 'start-setup.sh')],
                                    env=env, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            lines = calls.read_text().splitlines()
            self.assertEqual(len(lines), 2)
            self.assertTrue(lines[0].endswith('/installer-ui|ci --include=dev'))
            self.assertTrue(lines[1].endswith('/installer-ui|start'))
            self.assertFalse(list(work.glob('hermes-companion.*/source.zip')))


if __name__ == '__main__':
    unittest.main()
