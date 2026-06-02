const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('appInfo', {
    isElectron: true,
});

contextBridge.exposeInMainWorld('electronAPI', {
    readFile: (fileName) => ipcRenderer.invoke('read-file', fileName),
    writeFile: (fileName, content) => ipcRenderer.invoke('write-file', fileName, content),
    gitPublish: () => ipcRenderer.invoke('git-publish'),
});
