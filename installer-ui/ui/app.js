'use strict';
const $ = id => document.getElementById(id);
const bridge = window.hermesSetup;
const names = ['settings', 'checks', 'review', 'installing', 'finished'];
let inspection, running = false, awaitingOfficial = false, currentStage = -1;
function error(message = '') { $('error').textContent = message; $('error').hidden = !message; }
function show(name) {
  for (const item of names) $(item).hidden = item !== name;
  [...$('steps').children].forEach((li, index) => { if (index === names.indexOf(name)) li.setAttribute('aria-current', 'step'); else li.removeAttribute('aria-current'); });
  error(); $(name).querySelector('h1').focus(); window.scrollTo(0, 0);
}
function terminalBackend() { return document.querySelector('[name=terminal-backend]:checked').value; }
function desktopInstall() { return document.querySelector('[name=desktop-install]:checked').value; }
function settings() { return { accessPort: Number($('access-port').value), desktopInstall: desktopInstall(), terminalBackend: terminalBackend(), profile: $('profile').value.trim(), username: $('username').value.trim(), password: $('password').value, confirm: $('confirm').value, reset: $('reset').checked, accepted: $('accepted').checked }; }
function valid() {
  if (!$('settings-form').reportValidity()) return false;
  if (inspection.official.blocked || inspection.official.inProgress || (desktopInstall() === 'official' && !inspection.official.supported)) { error(inspection.official.message); return false; }
  if (/^(default|con|prn|aux|nul|com[1-9]|lpt[1-9])$/i.test($('profile').value.trim())) { error('Choose another profile name. Default and device names are reserved.'); return false; }
  if ($('password').value !== $('confirm').value) { error('The passwords do not match.'); $('confirm').focus(); return false; }
  return true;
}
function renderChecks() {
  $('check-list').replaceChildren();
  const checks = inspection.checks.map(check => desktopInstall() !== 'official' ? check : check.title === 'Hermes runtime' ? { ...check, detail: 'Managed by the original Desktop installer. The companion will require its completed runtime.' } : check.title === 'Mac build tools' ? { ...check, title: 'Optional component tools', detail: 'The original installer owns Hermes dependencies. The companion may use Homebrew for Docker/Tailscale.' } : check);
  if (desktopInstall() === 'official') checks.push({ title: 'Original Hermes Desktop', status: inspection.official.ready ? 'ready' : 'check', detail: inspection.official.message });
  for (const check of checks) {
    const li = document.createElement('li'), dot = document.createElement('span'), content = document.createElement('div'), title = document.createElement('b'), detail = document.createElement('p');
    dot.className = 'status-dot ' + check.status; dot.setAttribute('aria-hidden', 'true'); title.textContent = check.title + (check.status === 'ready' ? ' · detected' : check.status === 'blocked' ? ' · unsupported' : ' · checked during setup'); detail.textContent = check.detail;
    content.append(title, detail); li.append(dot, content); $('check-list').append(li);
  }
  $('platform-note').textContent = inspection.platform === 'win32'
    ? terminalBackend() === 'local' ? 'Local terminal mode runs on Windows directly. The installer skips Docker, WSL2 and virtualization-feature setup.' : 'Windows uses Docker Desktop’s internal WSL2 engine. No external Linux computer is required. If Windows requests a restart, reopen this wizard afterward.'
    : inspection.platform === 'darwin'
      ? desktopInstall() === 'official' ? 'The original installer handles Hermes Desktop on Apple Silicon. The companion configures the completed installation and optional terminal components.' : 'The explicit source-build alternative needs native build tools. Intel Mac source builds are best effort; an Apple Silicon-only DMG cannot be used.'
      : 'Linux setup currently supports apt-based desktop systems with systemd user services.';
  $('checks-next').disabled = !inspection.supported;
}
function review() {
  const s = settings(); $('review-settings').replaceChildren();
  for (const [label, value] of [['Desktop installation', s.desktopInstall === 'official' ? 'Original Nous Research installer' : 'Source build · advanced'], ['Profile', s.profile], ['Dashboard username', s.username], ['Password', 'Entered · hidden'], ['Existing login', s.reset ? 'Replace for this profile' : 'Keep if already configured'], ['Terminal', s.terminalBackend === 'docker' ? 'Docker sandbox' : 'Local terminal · this computer'], ['Private access', 'Tailscale TCP ' + s.accessPort]]) {
    const row = document.createElement('div'), dt = document.createElement('dt'), dd = document.createElement('dd'); dt.textContent = label; dd.textContent = value; row.append(dt, dd); $('review-settings').append(row);
  }
  $('network-review').textContent = 'Host Tailscale, authenticated Hermes backend and private TCP port ' + s.accessPort + '.';
  $('desktop-review').textContent = s.desktopInstall === 'official' ? 'The original Nous Research Desktop installer handles Hermes installation and dependencies. This companion reuses that completed installation.' : 'Native Hermes runtime and a local Desktop source build.';
  $('terminal-review').textContent = s.terminalBackend === 'docker' ? 'Docker for the terminal sandbox; a test container must run successfully.' : 'A local terminal that runs commands directly on this computer. Docker and WSL2 setup are skipped.';
  $('accepted').checked = false; $('install').disabled = true; show('review');
}
function setStage(name) {
  const rows = [...$('install-stages').children], index = rows.findIndex(li => li.dataset.stage === name);
  if (index < currentStage || index < 0) return;
  currentStage = index;
  rows.forEach((li, i) => { li.classList.toggle('done', i < index); li.classList.toggle('working', i === index); li.querySelector('small').textContent = i < index ? 'Completed' : i === index ? 'Working' : 'Waiting'; });
  $('progress-copy').textContent = rows[index].children[1].textContent + '. Follow any account or system dialogs that open.';
}
function event(data) {
  if (data.type === 'started') { awaitingOfficial = false; $('original-handoff').hidden = true; $('install-stages').hidden = false; $('activity').hidden = false; $('cancel').textContent = 'Stop installation'; running = true; currentStage = -1; $('log').textContent = ''; setStage('prerequisites'); }
  if (data.type === 'line') {
    $('log').textContent = ($('log').textContent + data.line + '\n').slice(-100000); $('log').scrollTop = $('log').scrollHeight;
    if (data.stage) setStage(data.stage);
  }
  if (data.type === 'input') { $('component-message').textContent = data.message; $('component-answer').type = data.secret ? 'password' : 'text'; $('component-input').hidden = false; $('component-answer').focus(); }
  if (data.type === 'input-cleared') { $('component-input').hidden = true; $('component-answer').value = ''; }
  if (data.type === 'finished') {
    running = false; $('component-answer').value = ''; $('component-input').hidden = true;
    $('finished-title').textContent = data.ok ? 'Installation checks complete.' : data.canceled ? 'Setup stopped.' : 'Setup needs attention.';
    $('finished-copy').textContent = data.ok ? 'Your local components passed the installer checks. Open Desktop to select your AI provider and model.' : data.message;
    $('report').textContent = data.ok ? data.report : $('log').textContent.slice(-12000);
    $('connection').hidden = !data.url; $('dashboard-address').textContent = data.url || '';
    $('open-desktop').hidden = !data.ok || !data.url; $('open-dashboard').hidden = !data.ok || !data.url;
    $('final-note').textContent = data.ok ? 'Still to verify: sign in to the dashboard from a second Tailscale device, then send a real message in Desktop. A configured TCP rule alone does not prove remote access.' : 'You can retry safely with the same profile name. Existing profiles and completed components are preserved. If a restart is required, restart the computer, reopen setup and re-enter your password.';
    show('finished');
  }
}
document.querySelectorAll('[data-back]').forEach(button => button.addEventListener('click', () => show(button.dataset.back)));
$('show-password').addEventListener('change', () => { $('password').type = $('confirm').type = $('show-password').checked ? 'text' : 'password'; });
$('settings-form').addEventListener('submit', async e => {
  e.preventDefault(); error(); if (!valid()) return;
  $('settings-next').disabled = true;
  try { inspection = await bridge.inspect(terminalBackend()); renderChecks(); show('checks'); } catch (e) { error(e.message); }
  finally { $('settings-next').disabled = false; }
});
$('checks-next').addEventListener('click', review);
$('accepted').addEventListener('change', () => { $('install').disabled = !$('accepted').checked; });
async function beginInstallation() {
  if (running) return;
  const value = settings(); if (!value.accepted) return;
  $('prerequisites-label').textContent = value.terminalBackend === 'docker' ? 'System prerequisites, Docker and Tailscale' : 'System prerequisites and Tailscale · local terminal';
  $('component-help').textContent = value.desktopInstall === 'official' ? 'The original installer opens in its own window and owns the Hermes installation. Complete its checks before returning here.' : 'Follow any Docker, Tailscale, Apple or Windows dialogs. Intel Mac source builds need native build tools and can take several minutes.';
  $('desktop-stage-label').textContent = value.desktopInstall === 'official' ? 'Original Desktop reuse and backend' : 'Hermes Desktop build and backend';
  $('install').disabled = true; $('check-original').disabled = true; show('installing');
  try {
    const result = await bridge.start(value);
    if (result.officialRequired) {
      awaitingOfficial = true;
      $('original-handoff').hidden = false; $('install-stages').hidden = true; $('activity').hidden = true;
      $('original-message').textContent = result.message;
      $('progress-copy').textContent = 'Your settings are ready. Complete the original installer first; then the companion applies your configuration.';
      $('cancel').textContent = 'Back to review';
    } else {
      $('password').value = $('confirm').value = ''; $('show-password').checked = false; $('password').type = $('confirm').type = 'password';
    }
  } catch (e) { running = false; awaitingOfficial = false; show('settings'); error(e.message); }
  finally { value.password = value.confirm = ''; $('check-original').disabled = false; $('install').disabled = !$('accepted').checked; }
}
$('install').addEventListener('click', beginInstallation);
$('check-original').addEventListener('click', beginInstallation);
$('open-original').addEventListener('click', async () => { try { await bridge.openOriginalInstaller(); } catch (e) { error(e.message); } });
$('component-input').addEventListener('submit', async e => { e.preventDefault(); const response = $('component-answer').value; $('component-answer').value = ''; try { await bridge.respond(response); } catch (e) { error(e.message); } });
$('manual-prompt').addEventListener('click', () => { $('component-message').textContent = 'Check the last installation message above and enter the requested response. Do not enter commands.'; $('component-answer').type = 'password'; $('component-input').hidden = false; $('component-answer').focus(); });
$('cancel').addEventListener('click', async () => { if (awaitingOfficial) { awaitingOfficial = false; show('review'); return; } if (window.confirm('Stop setup? Components already installed will be kept.')) await bridge.cancel(); });
$('retry').addEventListener('click', () => { $('accepted').checked = false; $('install').disabled = true; show('settings'); });
for (const [id, method] of [['open-dashboard', 'openDashboard'], ['open-desktop', 'openDesktop']]) $(id).addEventListener('click', async () => { try { await bridge[method](); } catch (e) { error(e.message); } });
function updateTerminalSummary() { $('terminal-summary').textContent = terminalBackend() === 'docker' ? 'Docker terminal sandbox' : 'Local terminal · this computer'; }
document.querySelectorAll('[name=terminal-backend]').forEach(input => input.addEventListener('change', updateTerminalSummary));
async function initialize() {
  if (!bridge) { $('system').textContent = 'Preview · installation is disabled'; error('Open the packaged Hermes Setup application to install. This browser preview cannot make system changes.'); return; }
  bridge.onEvent(event);
  try {
    inspection = await bridge.inspect(); $('system').textContent = inspection.system;
    const selectedMode = inspection.defaults.terminalBackend === 'local' ? 'local' : 'docker';
    document.querySelector('[name=terminal-backend][value=' + selectedMode + ']').checked = true;
    updateTerminalSummary();
    document.querySelector('[name=desktop-install][value=' + (inspection.defaults.desktopInstall === 'source' ? 'source' : 'official') + ']').checked = true;
    $('desktop-support-note').textContent = inspection.official.message;
    $('access-port').value = inspection.defaults.accessPort || 9119;
    $('profile').value = inspection.defaults.profile; $('username').value = inspection.defaults.username; $('soul').textContent = inspection.soul;
    $('settings-next').disabled = !inspection.supported; renderChecks();
    if (!inspection.supported) error('This computer is not supported. Review the system checks.');
  } catch (e) { error('Could not inspect this computer: ' + e.message); }
}
initialize();
