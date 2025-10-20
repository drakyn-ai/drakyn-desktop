// Preload script for exposing safe APIs to the renderer process
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electron', {
  // IPC event listeners
  ipcRenderer: {
    on: (channel, callback) => {
      ipcRenderer.on(channel, (event, ...args) => callback(event, ...args));
    },
    invoke: (channel, ...args) => {
      return ipcRenderer.invoke(channel, ...args);
    },
    send: (channel, ...args) => {
      ipcRenderer.send(channel, ...args);
    }
  }
});
