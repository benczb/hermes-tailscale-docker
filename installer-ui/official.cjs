'use strict';
const fs = require('node:fs/promises');
const path = require('node:path');
const os = require('node:os');

function officialInstaller(platform = process.platform, arch = process.arch) {
  if (platform === 'win32') return { supported: true, url: 'https://hermes-assets.nousresearch.com/Hermes-Setup.exe', label: 'Original Hermes Desktop installer for Windows' };
  if (platform === 'darwin' && arch === 'arm64') return { supported: true, url: 'https://hermes-assets.nousresearch.com/Hermes-Setup.dmg', label: 'Original Hermes Desktop installer for Apple Silicon' };
  return { supported: false, url: null, label: platform === 'darwin' ? 'The original DMG bootstrap installer is Apple Silicon-only. Intel Macs need an explicit source-build alternative.' : 'An original packaged Desktop installer is not currently published for Linux. The source-build alternative uses the official CLI installer.' };
}

// Mirror the original bootstrap installer's completion contract: its helper,
// a completion marker and a built app in the managed native checkout. An
// arbitrary `hermes` command on PATH is not sufficient to claim it completed.
async function officialInstallation({ platform = process.platform, arch = process.arch, home = os.homedir(), env = process.env, cliAvailable = false, bundledAppDetected = false } = {}) {
  const metadata = officialInstaller(platform, arch);
  const base = platform === 'win32' ? path.join(env.LOCALAPPDATA || '', 'hermes') : path.join(home, '.hermes');
  const checkout = path.join(base, 'hermes-agent');
  const helper = path.join(base, platform === 'win32' ? 'hermes-setup.exe' : 'hermes-setup');
  const release = path.join(checkout, 'apps/desktop/release');
  const candidates = platform === 'win32'
    ? ['win-unpacked/Hermes.exe', 'win-arm64-unpacked/Hermes.exe']
    : ['mac/Hermes.app/Contents/MacOS/Hermes', 'mac-arm64/Hermes.app/Contents/MacOS/Hermes'];
  const exists = async file => { try { return (await fs.stat(file)).isFile(); } catch { return false; } };
  if (platform === 'darwin') {
    for (const name of ['Hermes.app', 'Hermes Agent.app', 'HermesBundled.app']) {
      try { bundledAppDetected ||= (await fs.stat(path.join('/Applications', name, 'Contents/Resources/agent-payload'))).isDirectory(); } catch {}
    }
  }
  if (bundledAppDetected) return { ...metadata, ready: false, blocked: true, desktop: null, message: 'A bundled or Store edition of Hermes Desktop is already installed. This preview cannot yet map its runtime safely. Configure that installed app directly; the companion will not create another runtime or launch a second installer.' };
  if (await exists(path.join(base, '.hermes-update-in-progress'))) return { ...metadata, ready: false, inProgress: true, desktop: null, message: 'The original Hermes installer has an update in progress. Wait for it to finish before configuring Hermes. If it failed, use the original installer repair path.' };
  const [helperReady, markerReady, desktopPaths] = await Promise.all([
    exists(helper), exists(path.join(checkout, '.hermes-bootstrap-complete')),
    Promise.all(candidates.map(async rel => await exists(path.join(release, rel)) ? path.join(release, rel) : null))
  ]);
  const desktop = desktopPaths.find(Boolean) || null;
  const ready = metadata.supported && helperReady && markerReady && !!desktop && cliAvailable;
  return { ...metadata, ready, desktop, message: ready
    ? 'Original installer completion marker, installed Desktop and native CLI found. The companion will configure this installation without installing or rebuilding Hermes.'
    : !metadata.supported ? metadata.label
      : 'Run the original installer, complete its Desktop stage and open Hermes once. Then return here to check again. This companion will not install a second Hermes runtime.' };
}
module.exports = { officialInstaller, officialInstallation };
