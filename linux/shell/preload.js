'use strict';
/* Ponte minima e fixa entre a interface e a moldura: abrir/posicionar/fechar o app embutido e navegar (navegador). */
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('harumiHost', {
  embedOpen: (id, rect) => ipcRenderer.invoke('embed:open', String(id), rect),
  embedBounds: rect => ipcRenderer.send('embed:bounds', rect),
  embedClose: () => ipcRenderer.send('embed:close'),
  embedBack: () => ipcRenderer.send('embed:back'),
  embedPause: () => ipcRenderer.send('embed:pause'),
  embedType: text => ipcRenderer.send('embed:type', String(text || '')),
  embedFocus: () => ipcRenderer.send('embed:focus'),
  embedKey: name => ipcRenderer.send('embed:key', String(name || '')),
  embedMedia: cmd => ipcRenderer.send('embed:media', String(cmd)),
  onEmbedTitle: cb => ipcRenderer.on('embed:title', (e, t) => cb(String(t))),
  embedGo: text => ipcRenderer.send('embed:go', String(text || '')),
  onEmbedClosed: cb => ipcRenderer.on('embed:closed', (e, id) => cb(typeof id === 'string' ? id : '')),
  onEmbedUrl: cb => ipcRenderer.on('embed:url', (e, url) => cb(String(url)))
});
