'use strict';
const { test } = require('node:test');
const assert = require('node:assert/strict');
const { validateSettings, PrivateTranscript, CredentialPrompts, installCommand, installEnvironment, componentEvent, validProfileName } = require('../core.cjs');
const sample = () => ({ profile: 'Hamburger_01', username: 'Ben', password: 'A long private password!', confirm: 'A long private password!', accepted: true, reset: false });

test('preset validation prevents path/terminal input injection and requires review', () => {
  assert.equal(validateSettings(sample()).profile, 'Hamburger_01');
  for (const value of [undefined, null, {}, '', 'test', 'Test', 'root', 'sudo']) assert.equal(validProfileName(value), false);
  assert.equal(validProfileName('ben-personal'), true);
  for (const profile of ['../other', 'Default', 'hermes', 'test', 'Test', 'tmp', 'root', 'sudo', 'con', 'x\n', '-bad', 'x'.repeat(65)]) assert.throws(() => validateSettings({ ...sample(), profile }));
  for (const profile of ['ben-personal', 'starter-agent', 'test-agent', 'my-test']) assert.equal(validateSettings({ ...sample(), profile }).profile, profile);
  for (const patch of [{ username: ' ' }, { username: 'a\x1bb' }, { password: 'short' }, { password: 'long password\n' }, { confirm: 'other' }, { accepted: false }]) assert.throws(() => validateSettings({ ...sample(), ...patch }));
});
test('secret values never appear in process arguments or inherited environment', () => {
  const s = validateSettings(sample());
  for (const platform of ['win32', 'darwin', 'linux']) {
    const command = installCommand(s, '/trusted/bundle', platform);
    assert.ok(!JSON.stringify(command).includes(s.password));
    assert.ok(!JSON.stringify(installEnvironment(s, {})).includes(s.password));
    if (platform === 'win32') {
      assert.ok(command.args.includes('-SkipProfileSetup'));
      assert.ok(command.args.includes('-GuiMode'));
      assert.ok(command.args.includes(s.profile));
      assert.ok(!command.args.includes('-ResetDashboardAuth'));
      assert.ok(installCommand({ ...s, reset: true }, '/trusted/bundle', platform).args.includes('-ResetDashboardAuth'));
    }
  }
});
test('only known component events can request a guided wait; install retries stay manual', () => {
  assert.deepEqual(componentEvent('HERMES_SETUP_WAIT|docker|auto|Open Docker'), { type: 'component-wait', component: 'docker', automatic: true, message: 'Open Docker' });
  assert.equal(componentEvent('HERMES_SETUP_WAIT|tailscale|manual|Retry').automatic, false);
  assert.equal(componentEvent('HERMES_SETUP_READY|docker').type, 'component-ready');
  assert.equal(componentEvent('HERMES_SETUP_WAIT|buildtools|auto|Install Apple tools').component, 'buildtools');
  assert.equal(componentEvent('HERMES_SETUP_RESTART|Restart Windows').type, 'restart-required');
  for (const line of ['HERMES_SETUP_WAIT|arbitrary.exe|auto|run', 'prefix HERMES_SETUP_READY|docker', 'HERMES_SETUP_WAIT|docker|anything|run', 'HERMES_SETUP_WAIT|docker|auto|one\ntwo']) assert.equal(componentEvent(line), null);
  assert.equal(installEnvironment(validateSettings(sample()), {}).HERMES_GUI_MODE, '1');
});
test('terminal choice reaches both OS installers and rejects unknown backends', () => {
  assert.equal(validateSettings(sample()).terminalBackend, 'docker');
  for (const mode of ['docker', 'local']) {
    const settings = validateSettings({ ...sample(), terminalBackend: mode });
    assert.equal(installEnvironment(settings, {}).HERMES_TERMINAL_BACKEND, mode);
    const args = installCommand(settings, '/trusted/bundle', 'win32').args;
    assert.equal(args[args.indexOf('-TerminalBackend') + 1], mode);
  }
  for (const mode of ['ssh', '', null, 'local; command']) assert.throws(() => validateSettings({ ...sample(), terminalBackend: mode }));
});
test('credentials answer only exact known prompts, even across arbitrary chunks', () => {
  const s = validateSettings(sample()), sent = [];
  const router = new CredentialPrompts(s, value => sent.push(value));
  router.push('Password:'); assert.equal(sent.length, 0); // OS password must be entered explicitly.
  router.push('\nDashboard user'); router.push('name: ');
  router.push('\nShow password while typing? [y/N]: ');
  router.push('\nDashboard password (at least 12 characters; hidden): ');
  router.push('\nConfirm dashboard password (hidden): ');
  assert.deepEqual(sent, [s.username + '\r', 'n\r', s.password + '\r', s.password + '\r']);
  router.clear(); assert.equal(router.settings, null);
});
test('transcript redacts secrets split across any process output boundary', () => {
  const password = sample().password;
  for (let i = 0; i <= password.length; i++) {
    const lines = [], log = new PrivateTranscript([password], line => lines.push(line));
    log.push('prefix ' + password.slice(0, i)); log.push(password.slice(i) + '\n');
    assert.equal(lines.join(''), 'prefix [hidden]');
    log.hide('OS-private-pass'); log.push('OS-private-'); log.push('pass'); log.finish();
    assert.ok(!lines.join('').includes('OS-private-pass'));
  }
});
test('password is never used as an automatic response to an unrelated installer prompt', () => {
  const sent = [], router = new CredentialPrompts(validateSettings(sample()), answer => sent.push(answer));
  for (const prompt of ['Are you sure? [y/N]: ', 'Password: ', '[sudo] password for ben: ', 'API key: ', 'Dashboard password (visible): ']) router.push('\n' + prompt);
  assert.deepEqual(sent, []);
});
