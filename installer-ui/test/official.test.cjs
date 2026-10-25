'use strict';
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');
const { officialInstaller, officialInstallation } = require('../official.cjs');
const { validateSettings, installCommand, installEnvironment } = require('../core.cjs');
const sample = () => ({ profile: 'my_agent', username: 'my_login', password: 'Long fixture password!', confirm: 'Long fixture password!', accepted: true });

test('the original signed downloads are used only on supported platforms', () => {
  assert.equal(officialInstaller('win32', 'x64').url, 'https://hermes-assets.nousresearch.com/Hermes-Setup.exe');
  assert.equal(officialInstaller('darwin', 'arm64').url, 'https://hermes-assets.nousresearch.com/Hermes-Setup.dmg');
  assert.equal(officialInstaller('darwin', 'x64').supported, false);
  assert.equal(officialInstaller('linux', 'x64').supported, false);
});
test('official mode is the default and passes reuse-only flags to the companion', () => {
  const s = validateSettings(sample());
  assert.equal(s.desktopInstall, 'official');
  assert.equal(installEnvironment(s, {}).HERMES_USE_EXISTING_DESKTOP, '1');
  assert.ok(installCommand(s, '/trusted/scripts', 'win32').args.includes('-UseExistingDesktop'));
  const source = validateSettings({ ...sample(), desktopInstall: 'source' });
  assert.equal(installEnvironment(source, {}).HERMES_USE_EXISTING_DESKTOP, '0');
  assert.ok(!installCommand(source, '/trusted/scripts', 'win32').args.includes('-UseExistingDesktop'));
  assert.throws(() => validateSettings({ ...sample(), desktopInstall: 'image' }));
});
test('port defaults and custom values reach both platform scripts', () => {
  assert.equal(validateSettings(sample()).accessPort, 9119);
  const s = validateSettings({ ...sample(), accessPort: 9234 });
  assert.equal(installEnvironment(s, {}).HERMES_TAILNET_PORT, '9234');
  const args = installCommand(s, '/trusted/scripts', 'win32').args;
  assert.equal(args[args.indexOf('-TailnetPort') + 1], '9234');
  for (const accessPort of [0, 80, 65536, 9119.5, '', null, '9119; command']) assert.throws(() => validateSettings({ ...sample(), accessPort }));
});
test('an arbitrary CLI is not sufficient: require original installer completion and Desktop', async () => {
  const home = await fs.mkdtemp(path.join(os.tmpdir(), 'hermes-original-'));
  const base = path.join(home, '.hermes'), checkout = path.join(base, 'hermes-agent');
  const options = { platform: 'darwin', arch: 'arm64', home, cliAvailable: true };
  try {
    assert.equal((await officialInstallation(options)).ready, false);
    await fs.mkdir(checkout, { recursive: true });
    await fs.writeFile(path.join(checkout, '.hermes-bootstrap-complete'), '{}');
    await fs.writeFile(path.join(base, 'hermes-setup'), 'fixture');
    assert.equal((await officialInstallation(options)).ready, false);
    const desktop = path.join(checkout, 'apps/desktop/release/mac-arm64/Hermes.app/Contents/MacOS/Hermes');
    await fs.mkdir(path.dirname(desktop), { recursive: true }); await fs.writeFile(desktop, 'fixture');
    assert.equal((await officialInstallation(options)).ready, true);
    assert.equal((await officialInstallation({ ...options, cliAvailable: false })).ready, false);
    const updating = path.join(base, '.hermes-update-in-progress');
    await fs.writeFile(updating, 'fixture');
    assert.equal((await officialInstallation(options)).inProgress, true);
    await fs.rm(updating);
    const sealed = await officialInstallation({ ...options, bundledAppDetected: true });
    assert.equal(sealed.ready, false); assert.equal(sealed.blocked, true);
  } finally { await fs.rm(home, { recursive: true, force: true }); }
});
