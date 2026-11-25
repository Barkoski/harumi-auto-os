'use strict';
/* Moldura da Harumi (Electron). A interface vem do servidor local (127.0.0.1:8765); apps web como o YouTube
   abrem numa WebContentsView DENTRO da janela, na area que a interface reservar (card ou tela cheia). */
const { app, BrowserWindow, WebContentsView, ipcMain, session, shell } = require('electron');
const path = require('path');

const UI_ORIGIN = 'http://127.0.0.1:8765';
const UI_URL = UI_ORIGIN + '/assets/index.html';
// Logins (Google, Apple, Microsoft) entram na lista dos apps que precisam deles.
const LOGIN = ['google.com', 'gstatic.com', 'googleusercontent.com', 'apple.com', 'microsoftonline.com', 'live.com'];
const APPS = {
  youtube: { url: 'https://www.youtube.com/?hl=pt-BR&gl=BR', hosts: ['youtube.com', 'googlevideo.com', 'ytimg.com', 'youtube-nocookie.com'].concat(LOGIN) },
  claude: { url: 'https://claude.ai/', hosts: ['claude.ai', 'anthropic.com', 'claudeusercontent.com'].concat(LOGIN) },
  chatgpt: { url: 'https://chatgpt.com/', hosts: ['chatgpt.com', 'openai.com', 'oaistatic.com', 'oaiusercontent.com', 'auth0.com'].concat(LOGIN) },
  waze: { url: 'https://www.waze.com/pt-BR/live-map/', hosts: ['waze.com', 'googleapis.com', 'gstatic.com', 'google.com'] },
  browser: { url: 'https://www.google.com/?hl=pt-BR', anyHttps: true }
};

app.commandLine.appendSwitch('ozone-platform-hint', 'auto');
app.commandLine.appendSwitch('autoplay-policy', 'no-user-gesture-required');
app.commandLine.appendSwitch('lang', 'pt-BR');
if (process.env.HARUMI_DEBUG === '1') { // bancada (cdp.py), so local; desligada por padrao
  app.commandLine.appendSwitch('remote-debugging-address', '127.0.0.1');
  app.commandLine.appendSwitch('remote-debugging-port', '9222');
}

let win = null;
let embed = null; // { id, view }

function hostAllowed(id, url) {
  try {
    const u = new URL(url);
    if (u.protocol !== 'https:') return false;
    if (APPS[id].anyHttps) return true; // navegador: qualquer site https
    return APPS[id].hosts.some(d => u.hostname === d || u.hostname.endsWith('.' + d));
  } catch (e) { return false; }
}

/* Texto da barra do navegador -> URL https (ou busca no Google). */
function toUrl(text) {
  const t = String(text || '').trim().slice(0, 2000);
  if (!t) return null;
  if (/^https:\/\//i.test(t)) return t;
  if (/^[\w-]+(\.[\w-]+)+(\/\S*)?$/.test(t)) return 'https://' + t;
  return 'https://www.google.com/search?hl=pt-BR&q=' + encodeURIComponent(t);
}

function sanitizeRect(r) {
  const n = v => Math.max(0, Math.round(Number(v) || 0));
  return { x: n(r && r.x), y: n(r && r.y), width: n(r && r.width), height: n(r && r.height) };
}

// notify=false quando um app substitui outro: a tela nao deve receber "fechado" do app antigo.
function closeEmbed(notify = true) {
  if (!embed) return;
  const { view, id } = embed;
  embed = null;
  try { win.contentView.removeChildView(view); } catch (e) { /* janela fechando */ }
  try { view.webContents.close(); } catch (e) { /* ja fechada */ }
  if (notify && win && !win.isDestroyed()) win.webContents.send('embed:closed', id);
}

function openEmbed(id, rect) {
  if (!APPS[id] || !win) return false;
  if (embed && embed.id === id) { embed.view.setBounds(sanitizeRect(rect)); return true; }
  closeEmbed(false);
  const view = new WebContentsView({
    webPreferences: { partition: 'persist:harumi-apps', sandbox: true, contextIsolation: true }
  });
  view.setBackgroundColor('#111111');
  const wc = view.webContents;
  wc.setWindowOpenHandler(({ url }) => {
    if (hostAllowed(id, url)) wc.loadURL(url);
    return { action: 'deny' };
  });
  wc.on('will-navigate', (e, url) => { if (!hostAllowed(id, url)) e.preventDefault(); });
  wc.on('did-navigate', (e, url) => { if (win && !win.isDestroyed()) win.webContents.send('embed:url', url); });
  wc.on('did-navigate-in-page', (e, url) => { if (win && !win.isDestroyed()) win.webContents.send('embed:url', url); });
  wc.on('page-title-updated', (e, t) => { if (win && !win.isDestroyed()) win.webContents.send('embed:title', String(t).slice(0, 200)); });
  win.contentView.addChildView(view);
  view.setBounds(sanitizeRect(rect));
  wc.loadURL(APPS[id].url);
  embed = { id, view };
  return true;
}

function createWindow() {
  win = new BrowserWindow({
    fullscreen: true, kiosk: true, frame: false, backgroundColor: '#18151e', show: false,
    webPreferences: { preload: path.join(__dirname, 'preload.js'), contextIsolation: true, sandbox: true, nodeIntegration: false }
  });
  win.once('ready-to-show', () => win.show());
  win.webContents.setWindowOpenHandler(() => ({ action: 'deny' }));
  win.webContents.on('will-navigate', (e, url) => { if (!url.startsWith(UI_ORIGIN + '/')) e.preventDefault(); });
  // O servidor pode subir depois da moldura: tenta de novo ate carregar.
  const load = () => win.loadURL(UI_URL).catch(() => setTimeout(load, 1000));
  win.webContents.on('did-fail-load', (e, code, desc, url, isMain) => { if (isMain) setTimeout(load, 1000); });
  // Registra o motivo da queda (diagnostico) antes de recarregar a tela.
  win.webContents.on('render-process-gone', (e, d) => {
    try {
      const f = path.join(require('os').homedir(), '.cache/harumi/kiosk.log');
      require('fs').mkdirSync(path.dirname(f), { recursive: true });
      require('fs').appendFileSync(f, new Date().toISOString() + ' render-process-gone ' + JSON.stringify(d || {}) + '\n');
    } catch (err) { /* sem log */ }
    closeEmbed(); setTimeout(load, 500);
  });
  win.webContents.on('console-message', (e, level, message, line, sourceId) => {
    if (level < 3) return; // so erros
    try { require('fs').appendFileSync(path.join(require('os').homedir(), '.cache/harumi/kiosk.log'), new Date().toISOString() + ' console ' + String(message).slice(0, 300) + ' @' + String(sourceId).split('/').pop() + ':' + line + '\n'); } catch (err) { /* sem log */ }
  });
  app.on('child-process-gone', (e, d) => {
    try { require('fs').appendFileSync(path.join(require('os').homedir(), '.cache/harumi/kiosk.log'), new Date().toISOString() + ' child-process-gone ' + JSON.stringify(d || {}) + '\n'); } catch (err) { /* sem log */ }
  });
  load();
}

function fromUi(event) {
  return win && event.sender === win.webContents && event.senderFrame && event.senderFrame.url.startsWith(UI_ORIGIN + '/');
}

ipcMain.handle('embed:open', (e, id, rect) => fromUi(e) ? openEmbed(String(id), rect) : false);
ipcMain.on('embed:bounds', (e, rect) => {
  if (!fromUi(e) || !embed) return;
  const r = sanitizeRect(rect);
  embed.view.setVisible(r.width > 0 && r.height > 0); // area zero = escondido (outra tela por cima ou carro andando)
  embed.view.setBounds(r);
});
ipcMain.on('embed:close', e => { if (fromUi(e)) closeEmbed(); });
// Pausa qualquer video/audio do app embutido (bloqueio com o carro andando).
ipcMain.on('embed:pause', e => {
  if (!fromUi(e) || !embed) return;
  embed.view.webContents.executeJavaScript('document.querySelectorAll("video,audio").forEach(function(m){try{m.pause()}catch(x){}})', true).catch(() => {});
});
// Controles do mini-player para o app embutido (YouTube): tocar/pausar, anterior, proximo.
const MEDIA_JS = {
  toggle: 'var v=document.querySelector("video");if(v){v.paused?v.play():v.pause()}',
  next: 'var b=document.querySelector(".ytp-next-button");if(b)b.click()',
  prev: 'history.back()'
};
ipcMain.on('embed:media', (e, cmd) => {
  if (!fromUi(e) || !embed || !MEDIA_JS[cmd]) return;
  embed.view.webContents.executeJavaScript(MEDIA_JS[cmd], true).catch(() => {});
});
// Teclado na tela digitando no app embutido.
ipcMain.on('embed:type', (e, text) => { if (fromUi(e) && embed) embed.view.webContents.insertText(String(text).slice(0, 200)); });
ipcMain.on('embed:key', (e, name) => {
  if (!fromUi(e) || !embed || !['Backspace', 'Enter'].includes(name)) return;
  const wc = embed.view.webContents;
  wc.sendInputEvent({ type: 'keyDown', keyCode: name });
  if (name === 'Enter') wc.sendInputEvent({ type: 'char', keyCode: String.fromCharCode(13) });
  wc.sendInputEvent({ type: 'keyUp', keyCode: name });
});
// Antes do teclado na tela: coloca o cursor no campo de busca do app (YouTube) ou no campo ja ativo.
const FOCUS_JS = {
  youtube: '(function(){var i=document.querySelector("input[name=search_query]");if(i){i.focus();i.select&&i.select();return true}return false})()'
};
ipcMain.on('embed:focus', e => {
  if (!fromUi(e) || !embed) return;
  embed.view.webContents.focus();
  if (FOCUS_JS[embed.id]) embed.view.webContents.executeJavaScript(FOCUS_JS[embed.id], true).catch(() => {});
});
ipcMain.on('embed:go', (e, text) => {
  if (!fromUi(e) || !embed) return;
  const url = toUrl(text);
  if (url && hostAllowed(embed.id, url)) embed.view.webContents.loadURL(url);
});
ipcMain.on('embed:back', e => { if (fromUi(e) && embed && embed.view.webContents.navigationHistory.canGoBack()) embed.view.webContents.navigationHistory.goBack(); });

app.whenReady().then(() => {
  // Nenhuma permissao (camera, microfone, localizacao...) para os apps embutidos por enquanto.
  const apps = session.fromPartition('persist:harumi-apps');
  apps.setPermissionRequestHandler((wc, perm, cb) => cb(perm === 'fullscreen'));
  apps.setUserAgent(apps.getUserAgent(), 'pt-BR,pt'); // sites em portugues
  createWindow();
});
app.on('window-all-closed', () => app.quit());
app.on('web-contents-created', (e, wc) => { wc.on('will-attach-webview', ev => ev.preventDefault()); });
void shell; // nao abre nada fora da Harumi
