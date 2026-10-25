'use strict';
const { app, BrowserWindow, ipcMain, dialog, shell } = require('electron');
const { execFile, spawn } = require('node:child_process');
const { promisify } = require('node:util');
const fs = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const core = require('./core.cjs');
const exec = promisify(execFile);
let window, task, transcript, prompts, activeProfile, dashboardUrl, canceled = false, awaitingInput = false, starting = false;
const root = () => app.isPackaged ? path.join(process.resourcesPath, 'installer') : path.resolve(__dirname, '../scripts');
const page = pathToFileURL(path.join(__dirname, 'ui/index.html')).href;
const send = data => { if (window && !window.isDestroyed()) window.webContents.send('setup:event', data); };
function hostEnvironment() {
  const env = { ...process.env };
  const extra = process.platform === 'win32'
    ? [path.join(env.LOCALAPPDATA || '', 'hermes/bin'), path.join(env.ProgramFiles || 'C:\\Program Files', 'Docker/Docker/resources/bin'), path.join(env.ProgramFiles || 'C:\\Program Files', 'Tailscale')]
    : [path.join(os.homedir(), '.local/bin'), '/opt/homebrew/bin', '/usr/local/bin', '/Applications/Docker.app/Contents/Resources/bin'];
  env.PATH = [...extra, env.PATH || ''].join(path.delimiter);
  return env;
}
async function probe(file, args) {
  try { const { stdout } = await exec(file, args, { timeout: 15000, windowsHide: true, env: hostEnvironment(), maxBuffer: 1024 * 1024 }); return { ok: true, output: stdout.replace(/\0/g, '').trim() }; }
  catch { return { ok: false, output: '' }; }
}
async function inspect() {
  const platform = process.platform;
  const supported = ['win32', 'darwin', 'linux'].includes(platform) && ['x64', 'arm64'].includes(os.arch()) && !(platform === 'linux' && /microsoft|wsl/i.test(os.release()));
  const [docker, tailscale, hermes, brew, wsl] = await Promise.all([
    probe('docker', ['info', '--format', '{{.OSType}}']),
    probe(platform === 'darwin' ? '/Applications/Tailscale.app/Contents/MacOS/Tailscale' : 'tailscale', ['status', '--json']),
    platform === 'win32'
      ? probe('powershell.exe', ['-NoProfile', '-Command', 'if (Get-Command hermes -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }'])
      : probe('/usr/bin/which', ['hermes']),
    platform === 'darwin' ? probe('brew', ['--version']) : Promise.resolve(null),
    platform === 'win32' ? probe('wsl.exe', ['--version']) : Promise.resolve(null)
  ]);
  let tailConnected = false;
  try { tailConnected = JSON.parse(tailscale.output).BackendState === 'Running'; } catch {}
  let saved = {};
  try { saved = JSON.parse(await fs.readFile(path.join(app.getPath('userData'), 'settings.json'), 'utf8')); } catch {}
  const soulPath = app.isPackaged ? path.join(root(), 'SOUL.md') : path.resolve(__dirname, '../profiles/workshop/SOUL.md');
  return {
    platform, architecture: os.arch(), system: `${os.type()} ${os.release()} · ${os.arch()}`, supported,
    defaults: { profile: saved.profile || '', username: saved.username || '', reset: false },
    checks: [
      { title: 'This computer', status: supported ? 'ready' : 'blocked', detail: supported ? 'Native installation on this computer.' : 'Use a native 64-bit Windows, macOS or Linux desktop; WSL is not the installer host.' },
      ...(wsl ? [{ title: 'Windows WSL2', status: 'check', detail: wsl.ok ? 'Detected. The installer will check compatibility and update if needed; a restart may be required.' : 'The installer will enable or update WSL2 for Docker. A restart may be required.' }] : []),
      ...(brew ? [{ title: 'Mac build tools', status: 'check', detail: brew.ok ? 'Homebrew found. OpenSSL and build tools will be checked.' : 'Homebrew will be installed. Xcode Command Line Tools may need an Apple setup dialog.' }] : []),
      { title: 'Docker terminal sandbox', status: docker.ok && docker.output === 'linux' ? 'ready' : 'check', detail: docker.ok && docker.output === 'linux' ? 'Engine responds; installation will also run a test container.' : 'Docker needs installation, startup or configuration.' },
      { title: 'Host Tailscale', status: tailConnected ? 'ready' : 'check', detail: tailConnected ? 'Connected. TCP forwarding will be configured after the authenticated backend is ready.' : 'Install or sign in to Tailscale during setup.' },
      { title: 'Hermes runtime', status: hermes.ok ? 'ready' : 'check', detail: hermes.ok ? 'An existing native command is available. The installer will reuse it.' : 'A native Hermes runtime will be installed.' }
    ],
    soul: await fs.readFile(soulPath, 'utf8')
  };
}
function trusted(event) {
  if (!window || event.sender !== window.webContents || event.senderFrame !== window.webContents.mainFrame || event.senderFrame.url !== page) throw new Error('Untrusted setup request.');
}
function handler(name, fn) { ipcMain.handle(name, async (event, ...args) => { trusted(event); return fn(...args); }); }

handler('setup:inspect', inspect);
handler('setup:start', async input => {
  if (task || starting) throw new Error('An installation is already running.');
  starting = true;
  try {
  const settings = core.validateSettings(input);
  if (!(await inspect()).supported) throw new Error('This computer is not supported.');
  if (process.platform !== 'win32' && process.getuid?.() === 0) throw new Error('Open Hermes Setup using your normal desktop account, not root.');
  // No password is serialized, passed in argv/environment or saved for resume.
  await fs.mkdir(app.getPath('userData'), { recursive: true, mode: 0o700 });
  await fs.writeFile(path.join(app.getPath('userData'), 'settings.json'), JSON.stringify({ profile: settings.profile, username: settings.username }), { mode: 0o600 });
  activeProfile = settings.profile;
  dashboardUrl = null;
  canceled = false;
  transcript = new core.PrivateTranscript([settings.password], line => send({ type: 'line', line, stage: core.stageFromLine(line) }));
  const command = core.installCommand(settings, root());
  const pty = require('node-pty');
  task = pty.spawn(command.file, command.args, {
    name: 'xterm-256color', cols: 120, rows: 40, cwd: root(),
    env: core.installEnvironment(settings, hostEnvironment())
  });
  prompts = new core.CredentialPrompts(settings, answer => task.write(answer));
  send({ type: 'started' });
  awaitingInput = false;
  task.onData(chunk => {
    transcript.push(chunk);
    const answered = prompts.push(chunk);
    if (answered) { awaitingInput = false; send({ type: 'input-cleared' }); return; }
    const tail = prompts.tail;
    const match = tail.match(/(?:^|\n)([^\n]{0,300}(?:password\s*:|\[sudo\][^\n]*:|\[y\/n\][^\n]*|\[yes\/no\][^\n]*|press (?:return|enter)[^\n]*))\s*$/i);
    if (!awaitingInput && match) {
      awaitingInput = true;
      send({ type: 'input', message: transcript.redact(match[1]), secret: /password/i.test(match[1]) });
    }
  });
  task.onExit(async ({ exitCode }) => {
    transcript.finish();
    prompts.clear(); prompts = null; task = null;
    if (canceled) { send({ type: 'finished', ok: false, canceled: true, message: 'Installation stopped. Completed components are kept; reopen setup to resume.' }); return; }
    if (exitCode !== 0) { send({ type: 'finished', ok: false, message: 'Setup stopped. Review the last messages below. If Windows requires a restart, restart it and reopen this wizard; re-enter your password to resume.' }); return; }
    try {
      const report = await fs.readFile(core.readinessPath(activeProfile), 'utf8');
      if (!report.includes('INSTALLATION CHECKS COMPLETE')) throw new Error('Missing completion report.');
      const url = report.match(/Tailnet URL: (http:\/\/100\.\d{1,3}\.\d{1,3}\.\d{1,3}:9119)/)?.[1];
      dashboardUrl = url || null;
      send({ type: 'finished', ok: true, report, url: dashboardUrl });
    } catch { send({ type: 'finished', ok: false, message: 'The setup process exited, but its verification report is missing. Completion has not been confirmed.' }); }
  });
  return { started: true };
  } finally { starting = false; }
});
handler('setup:respond', input => {
  if (!task || !prompts || typeof input !== 'string' || input.length > 1024 || /[\x00-\x1f\x7f]/.test(input)) throw new Error('Invalid setup response.');
  // Treat every manual response as sensitive, even if the prompt is not a password.
  transcript.hide(input); prompts.tail = ''; awaitingInput = false; task.write(input + '\r');
  send({ type: 'input-cleared' });
});
handler('setup:cancel', () => { if (task) { canceled = true; task.kill(); } });
handler('setup:dashboard', async () => { if (!dashboardUrl) throw new Error('No verified dashboard address is available.'); await shell.openExternal(dashboardUrl); });
handler('setup:desktop', async () => {
  if (task || !activeProfile || !dashboardUrl) throw new Error('Complete installation first.');
  const env = hostEnvironment(); delete env.HERMES_HOME; delete env.HERMES_DESKTOP_REMOTE_URL;
  const file = process.platform === 'win32' ? path.join(env.LOCALAPPDATA, 'hermes/bin/hermes.exe') : path.join(os.homedir(), '.local/bin/hermes');
  const child = spawn(file, ['-p', activeProfile, 'desktop'], { env, detached: true, stdio: 'ignore', windowsHide: true });
  return new Promise((resolve, reject) => { child.once('error', () => reject(new Error('Desktop could not be launched. Check the native Hermes installation.'))); child.once('spawn', () => { child.unref(); resolve(); }); });
});

if (!app.requestSingleInstanceLock()) app.quit();
else app.whenReady().then(() => {
  window = new BrowserWindow({ width: 1060, height: 820, minWidth: 760, minHeight: 650, title: 'Hermes Setup', backgroundColor: '#f6f7f9', autoHideMenuBar: true,
    webPreferences: { preload: path.join(__dirname, 'preload.cjs'), contextIsolation: true, sandbox: true, nodeIntegration: false, webSecurity: true } });
  window.webContents.setWindowOpenHandler(() => ({ action: 'deny' }));
  window.webContents.on('will-navigate', event => event.preventDefault());
  window.webContents.session.setPermissionRequestHandler((_contents, _permission, callback) => callback(false));
  window.on('close', event => {
    if (task) {
      const choice = dialog.showMessageBoxSync(window, { type: 'warning', buttons: ['Keep installing', 'Stop and close'], defaultId: 0, cancelId: 0, message: 'Installation is still running.', detail: 'Stopping keeps components already installed. You can reopen setup to retry.' });
      if (choice === 0) event.preventDefault(); else { canceled = true; task.kill(); }
    }
  });
  window.loadURL(page);
});
app.on('second-instance', () => { if (window) { window.restore(); window.focus(); } });
app.on('window-all-closed', () => app.quit());
