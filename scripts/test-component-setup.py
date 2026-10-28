"""Test the production Bash component loops without running the installer."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipIf(os.name == 'nt', 'POSIX Bash fixture')
class ComponentSetup(unittest.TestCase):
    def test_install_retry_and_readiness_wait_keep_one_session(self):
        source = (ROOT / 'scripts/setup-macos-linux.sh').read_text()
        helpers = source[source.index('component_step()'):source.index('[ "$(id -u)"')]
        with tempfile.TemporaryDirectory() as fixture:
            script = Path(fixture) / 'fixture.sh'
            script.write_text('set -euo pipefail\nfail() { echo "$*" >&2; exit 1; }\ngui_mode=1\n' + helpers + '''
attempts=0
install_fake() { attempts=$((attempts+1)); [ "$attempts" -ge 2 ]; }
component_step docker 'Retry Docker install' install_fake
[ "$attempts" = 2 ]
checks=0
ready_fake() { checks=$((checks+1)); [ "$checks" -ge 3 ]; }
component_wait tailscale 'Connect Tailscale' ready_fake
[ "$checks" = 3 ]
''')
            result = subprocess.run(['/bin/bash', str(script)], input='\n\n\n', text=True, capture_output=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(result.stdout.count('HERMES_SETUP_WAIT|docker|manual|'), 1)
            self.assertEqual(result.stdout.count('HERMES_SETUP_WAIT|tailscale|auto|'), 2)
            self.assertIn('HERMES_SETUP_READY|tailscale', result.stdout)


if __name__ == '__main__':
    unittest.main()
