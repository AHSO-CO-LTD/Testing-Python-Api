const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electron', {
  getAppVersion: () => ipcRenderer.invoke('app-version'),
  isPlatform: (platform) => process.platform === platform,
});

// Expose ipcRenderer if needed (restricted)
contextBridge.exposeInMainWorld('ipcRenderer', {
  send: (channel, ...args) => {
    if (['app-version'].includes(channel)) {
      ipcRenderer.send(channel, ...args);
    }
  },
  on: (channel, listener) => {
    if (['app-version'].includes(channel)) {
      ipcRenderer.on(channel, (_event, ...args) => listener(...args));
    }
  },
});
