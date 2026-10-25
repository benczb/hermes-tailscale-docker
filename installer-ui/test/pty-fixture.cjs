'use strict';
const readline = require('node:readline');
const input = readline.createInterface({ input: process.stdin, output: process.stdout });
const ask = text => new Promise(resolve => input.question(text, resolve));
(async () => {
  const username = await ask('Dashboard username: ');
  const visibility = await ask('Show password while typing? [y/N]: ');
  const password = await ask('Dashboard password (at least 12 characters; hidden): ');
  const confirmation = await ask('Confirm dashboard password (hidden): ');
  input.close();
  if (username !== 'smoke-user' || visibility !== 'n' || password !== 'private-smoke-password' || confirmation !== password) process.exit(1);
  console.log('PRESETS_OK');
})().catch(() => process.exit(1));
