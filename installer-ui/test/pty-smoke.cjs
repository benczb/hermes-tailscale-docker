'use strict';
// Exercise the native PTY in Electron's own Node runtime. No package manager,
// installer, administrator command or host service is run by this smoke test.
const assert = require('node:assert/strict');
const { spawnSync } = require('node:child_process');
const path = require('node:path');
if (!process.versions.electron) {
  const result = spawnSync(require('electron'), [__filename], { env: { ...process.env, ELECTRON_RUN_AS_NODE: '1' }, stdio: 'inherit', timeout: 30000 });
  if (result.error) throw result.error;
  process.exit(result.status ?? 1);
}
const pty = require('node-pty');
const { CredentialPrompts, PrivateTranscript } = require('../core.cjs');
const settings = { username: 'smoke-user', password: 'private-smoke-password' };
const log = [], transcript = new PrivateTranscript([settings.password], line => log.push(line));
const child = pty.spawn(process.execPath, [path.join(__dirname, 'pty-fixture.cjs')], {
  cols: 120, rows: 40, env: { ...process.env, ELECTRON_RUN_AS_NODE: '1' }, cwd: __dirname
});
const prompts = new CredentialPrompts(settings, answer => child.write(answer));
const deadline = setTimeout(() => { child.kill(); process.exit(1); }, 20000);
child.onData(chunk => { transcript.push(chunk); prompts.push(chunk); });
child.onExit(({ exitCode }) => {
  clearTimeout(deadline); transcript.finish(); prompts.clear();
  assert.equal(exitCode, 0, log.join('\n'));
  assert.ok(log.join('\n').includes('PRESETS_OK'));
  assert.ok(!log.join('\n').includes(settings.password));
  console.log('Electron native PTY: preset bridge and output redaction passed.');
});
