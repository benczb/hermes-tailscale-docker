'use strict';
const os = require('node:os');
const path = require('node:path');

const RESERVED = /^(default|con|prn|aux|nul|com[1-9]|lpt[1-9])$/i;
function validateSettings(input) {
  if (!input || typeof input !== 'object') throw new Error('Enter your setup settings.');
  const rawProfile = String(input.profile || '');
  const rawUsername = String(input.username || '');
  if (/[\x00-\x1f\x7f]/.test(rawProfile + rawUsername)) throw new Error('Names must not contain line breaks or control characters.');
  const profile = rawProfile.trim();
  const username = rawUsername.trim();
  const password = String(input.password || '');
  const terminalBackend = input.terminalBackend === undefined ? 'docker' : input.terminalBackend;
  if (!['docker', 'local'].includes(terminalBackend)) throw new Error('Choose Docker sandbox or local terminal.');
  const desktopInstall = input.desktopInstall === undefined ? 'official' : input.desktopInstall;
  if (!['official', 'source'].includes(desktopInstall)) throw new Error('Choose the original Desktop installer or the explicit source-build alternative.');
  const rawPort = input.accessPort === undefined ? 9119 : input.accessPort;
  if (!/^\d{1,5}$/.test(String(rawPort))) throw new Error('Enter a whole-number TCP port. Default: 9119.');
  const accessPort = Number(rawPort);
  if (!Number.isInteger(accessPort) || accessPort < 1024 || accessPort > 65535) throw new Error('Choose a TCP port from 1024 to 65535. Default: 9119.');
  if (!/^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$/.test(profile) || RESERVED.test(profile)) {
    throw new Error('Profile name: use 1–64 letters, digits, underscores or hyphens, starting with a letter or digit. Default and device names are reserved.');
  }
  if (!username || username.length > 128 || /[\x00-\x1f\x7f]/.test(username)) throw new Error('Enter a dashboard username without control characters.');
  if (password.length < 12 || password.length > 256 || /[\x00-\x1f\x7f]/.test(password)) throw new Error('Use a password of 12–256 characters without line breaks or control characters.');
  if (password !== input.confirm) throw new Error('The passwords do not match.');
  if (input.accepted !== true) throw new Error('Review and accept the installation choices first.');
  return { profile, username, password, reset: input.reset === true, terminalBackend, desktopInstall, accessPort };
}

function stripTerminal(value) {
  return value.replace(/\x1b\][^\x07]*(?:\x07|\x1b\\)/g, '')
    .replace(/\x1b\[[0-?]*[ -/]*[@-~]/g, '').replace(/\r/g, '').replace(/[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]/g, '');
}

// Hold incomplete lines so secrets split across process chunks cannot reach the UI.
class PrivateTranscript {
  constructor(secrets, emit) { this.secrets = [...secrets]; this.pending = ''; this.emit = emit; }
  hide(value) { if (value) this.secrets.push(value); }
  redact(value) {
    let text = stripTerminal(value);
    for (const secret of this.secrets.sort((a, b) => b.length - a.length)) text = text.split(secret).join('[hidden]');
    return text;
  }
  push(chunk) {
    this.pending += chunk;
    const lines = this.pending.split('\n');
    this.pending = lines.pop();
    for (const line of lines) this.emit(this.redact(line));
    // Progress animations can produce unbounded output without newlines. Keep a
    // bounded tail; never flush an unredacted partial credential into the renderer.
    if (this.pending.length > 65536) this.pending = this.pending.slice(-32768);
  }
  finish() { if (this.pending) this.emit(this.redact(this.pending)); this.pending = ''; }
}

class CredentialPrompts {
  constructor(settings, write) { this.settings = settings; this.write = write; this.tail = ''; }
  push(chunk) {
    this.tail = (this.tail + stripTerminal(chunk)).slice(-4096);
    const patterns = [
      [/Dashboard username\s*:\s*$/i, this.settings.username],
      [/Show password while typing\? \[y\/N\]\s*:\s*$/i, 'n'],
      [/Dashboard password \(at least 12 characters; hidden\)\s*:\s*$/i, this.settings.password],
      [/Confirm dashboard password \(hidden\)\s*:\s*$/i, this.settings.password]
    ];
    for (const [pattern, answer] of patterns) {
      if (pattern.test(this.tail)) { this.tail = ''; this.write(answer + '\r'); return true; }
    }
    return false;
  }
  clear() { this.tail = ''; this.settings = null; }
}

function installCommand(settings, root, platform = process.platform) {
  if (platform === 'win32') return {
    file: 'powershell.exe',
    args: ['-NoLogo', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', path.join(root, 'setup-windows.ps1'), '-ProfileName', settings.profile, '-TerminalBackend', settings.terminalBackend || 'docker', '-TailnetPort', String(settings.accessPort || 9119), '-SkipProfileSetup', ...(settings.desktopInstall === 'official' ? ['-UseExistingDesktop'] : []), ...(settings.reset ? ['-ResetDashboardAuth'] : [])]
  };
  return { file: '/bin/bash', args: [path.join(root, 'setup-macos-linux.sh')] };
}
function installEnvironment(settings, inherited = process.env) {
  return { ...inherited, HERMES_PROFILE_NAME: settings.profile, HERMES_TERMINAL_BACKEND: settings.terminalBackend || 'docker', HERMES_TAILNET_PORT: String(settings.accessPort || 9119), HERMES_USE_EXISTING_DESKTOP: settings.desktopInstall === 'official' ? '1' : '0', HERMES_SKIP_PROFILE_SETUP: '1', HERMES_RESET_DASHBOARD_AUTH: settings.reset ? '1' : '0', TERM: 'xterm-256color' };
}
function readinessPath(profile, platform = process.platform, env = process.env) {
  return platform === 'win32'
    ? path.join(env.LOCALAPPDATA, 'HermesWorkshopInstaller', profile, 'installation-ready.txt')
    : path.join(os.homedir(), '.hermes-workshop-installer', profile, 'installation-ready.txt');
}
function stageFromLine(line) {
  if (/INSTALLATION CHECKS COMPLETE/.test(line)) return 'verify';
  if (/serve status|Ready: http:|Tailnet URL:|Tailscale TCP \d+/.test(line)) return 'network';
  if (/Building\/checking Hermes Desktop|build-only|building.*desktop|Reusing Hermes Desktop/i.test(line)) return 'desktop';
  if (/Using Hermes profile:|Configuring the (?:docker|local) terminal|Choose your Hermes dashboard login|Keeping existing profile:/.test(line)) return 'profile';
  if (/Hermes Agent Installer|Hermes Agent cloned|Installing the latest stable/.test(line)) return 'runtime';
  return null;
}
module.exports = { validateSettings, stripTerminal, PrivateTranscript, CredentialPrompts, installCommand, installEnvironment, readinessPath, stageFromLine };
