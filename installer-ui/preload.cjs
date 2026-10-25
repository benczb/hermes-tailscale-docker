'use strict';
const { contextBridge, ipcRenderer } = require('electron');
contextBridge.exposeInMainWorld('hermesSetup', {
  inspect: terminalBackend => ipcRenderer.invoke('setup:inspect', terminalBackend),
  start: settings => ipcRenderer.invoke('setup:start', settings),
  respond: response => ipcRenderer.invoke('setup:respond', response),
  cancel: () => ipcRenderer.invoke('setup:cancel'),
  openDashboard: () => ipcRenderer.invoke('setup:dashboard'),
  openDesktop: () => ipcRenderer.invoke('setup:desktop'),
  onEvent: listener => {
    const handle = (_event, data) => listener(data);
    ipcRenderer.on('setup:event', handle);
    return () => ipcRenderer.removeListener('setup:event', handle);
  }
});
