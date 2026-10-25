'use strict';
const $ = id => document.getElementById(id);
const bridge = window.hermesSetup;
const names = ['settings', 'checks', 'review', 'installing', 'finished'];
let inspection, running = false, currentStage = -1;
function error(message = '') { $('error').textContent = message; $('error').hidden = !message; }
function show(name) {
  for (const item of names) $(item).hidden = item !== name;
  [...$('steps').children].forEach((li, index) => { if (index === names.indexOf(name)) li.setAttribute('aria-current', 'step'); else li.removeAttribute('aria-current'); });
  error(); $(name).querySelector('h1').focus(); window.scrollTo(0, 0);
}
function settings() { return { profile: $('profile').value.trim(), username: $('username').value.trim(), password: $('password').value, confirm: $('confirm').value, reset: $('reset').checked, accepted: $('accepted').checked }; }
function valid() {
  if (!$('settings-form').reportValidity()) return false;
  if (/^(default|con|prn|aux|nul|com[1-9]|lpt[1-9])$/i.test($('profile').value.trim())) { error('Choose another profile name. Default and device names are reserved.'); return false; }
  if ($('password').value !== $('confirm').value) { error('The passwords do not match.'); $('confirm').focus(); return false; }
  return true;
}
function renderChecks() {
  $('check-list').replaceChildren();
  for (const check of inspection.checks) {
    const li = document.createElement('li'), dot = document.createElement('span'), content = document.createElement('div'), title = document.createElement('b'), detail = document.createElement('p');
    dot.className = 'status-dot ' + check.status; dot.setAttribute('aria-hidden', 'true'); title.textContent = check.title + (check.status === 'ready' ? ' · detected' : check.status === 'blocked' ? ' · unsupported' : ' · checked during setup'); detail.textContent = check.detail;
    content.append(title, detail); li.append(dot, content); $('check-list').append(li);
  }
  $('platform-note').textContent = inspection.platform === 'win32'
    ? 'Windows uses Docker Desktop’s internal WSL2 engine. No external Linux computer is required. If Windows requests a restart, reopen this wizard afterward.'
    : inspection.platform === 'darwin'
      ? 'Mac setup builds Hermes Desktop locally. Intel Macs need the Intel source-build path; an Apple Silicon-only DMG cannot be used. Homebrew and Xcode setup may need your attention.'
      : 'Linux setup currently supports apt-based desktop systems with systemd user services.';
  $('checks-next').disabled = !inspection.supported;
}
function review() {
  const s = settings(); $('review-settings').replaceChildren();
  for (const [label, value] of [['Profile', s.profile], ['Dashboard username', s.username], ['Password', 'Entered · hidden'], ['Existing login', s.reset ? 'Replace for this profile' : 'Keep if already configured'], ['Terminal', 'Docker sandbox'], ['Private access', 'Tailscale TCP 9119']]) {
    const row = document.createElement('div'), dt = document.createElement('dt'), dd = document.createElement('dd'); dt.textContent = label; dd.textContent = value; row.append(dt, dd); $('review-settings').append(row);
  }
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
  if (data.type === 'started') { running = true; currentStage = -1; $('log').textContent = ''; setStage('prerequisites'); }
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
  try { inspection = await bridge.inspect(); renderChecks(); show('checks'); } catch (e) { error(e.message); }
  finally { $('settings-next').disabled = false; }
});
$('checks-next').addEventListener('click', review);
$('accepted').addEventListener('change', () => { $('install').disabled = !$('accepted').checked; });
$('install').addEventListener('click', async () => {
  if (running) return;
  const value = settings(); if (!value.accepted) return;
  $('install').disabled = true; show('installing');
  try { await bridge.start(value); $('password').value = $('confirm').value = ''; $('show-password').checked = false; $('password').type = $('confirm').type = 'password'; }
  catch (e) { running = false; show('settings'); error(e.message); }
  finally { value.password = value.confirm = ''; }
});
$('component-input').addEventListener('submit', async e => { e.preventDefault(); const response = $('component-answer').value; $('component-answer').value = ''; try { await bridge.respond(response); } catch (e) { error(e.message); } });
$('manual-prompt').addEventListener('click', () => { $('component-message').textContent = 'Check the last installation message above and enter the requested response. Do not enter commands.'; $('component-answer').type = 'password'; $('component-input').hidden = false; $('component-answer').focus(); });
$('cancel').addEventListener('click', async () => { if (window.confirm('Stop setup? Components already installed will be kept.')) await bridge.cancel(); });
$('retry').addEventListener('click', () => { $('accepted').checked = false; $('install').disabled = true; show('settings'); });
for (const [id, method] of [['open-dashboard', 'openDashboard'], ['open-desktop', 'openDesktop']]) $(id).addEventListener('click', async () => { try { await bridge[method](); } catch (e) { error(e.message); } });
async function initialize() {
  if (!bridge) { $('system').textContent = 'Preview · installation is disabled'; error('Open the packaged Hermes Setup application to install. This browser preview cannot make system changes.'); return; }
  bridge.onEvent(event);
  try {
    inspection = await bridge.inspect(); $('system').textContent = inspection.system;
    $('profile').value = inspection.defaults.profile; $('username').value = inspection.defaults.username; $('soul').textContent = inspection.soul;
    $('settings-next').disabled = !inspection.supported; renderChecks();
    if (!inspection.supported) error('This computer is not supported. Review the system checks.');
  } catch (e) { error('Could not inspect this computer: ' + e.message); }
}
initialize();
