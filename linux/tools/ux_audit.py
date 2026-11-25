#!/usr/bin/env python3
"""Auditoria de UX da Harumi, roda NA placa (so biblioteca padrao), usando cdp.py vizinho.

  cd ~/harumi && python3 ux_audit.py > auditoria.json

Para cada tela (inicial, gaveta, ajustes, conversa, painel do carro, teclado) mede alvos de toque < 44 px,
textos < 14 px, botoes sem nome acessivel e contraste aproximado < 4.5:1 (texto < 18 px). Tambem recarrega a
pagina e escuta ~12 s por erros de console e violacoes de CSP. Saida: JSON em stdout, codigo de saida 0.
Variaveis: CDP_PORT, CDP_MATCH (como no cdp.py).
"""
import json
import os
import socket
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdp  # noqa: E402

LIMITE = 30
ESCUTA_S = 12

# Medicao feita dentro da pagina. Retorna JSON (string) com quatro listas.
JS_MEDIR = r"""
(function () {
  var IGN = '.maplibregl-ctrl-attrib, .leaflet-control-attribution, #nav-credit';
  var vw = innerWidth, vh = innerHeight;
  function desc(el) {
    var s = el.tagName.toLowerCase();
    if (el.id) s += '#' + el.id;
    var c = (typeof el.className === 'string' ? el.className : '').trim().split(/\s+/).filter(Boolean).slice(0, 3);
    if (c.length) s += '.' + c.join('.');
    return s;
  }
  function visivel(el) {
    var r = el.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0) return null;
    if (r.right <= 0 || r.bottom <= 0 || r.left >= vw || r.top >= vh) return null;
    for (var n = el; n && n.nodeType === 1; n = n.parentElement) {
      var cs = getComputedStyle(n);
      if (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) === 0) return null;
    }
    return r;
  }
  function rgba(str) {
    var m = /rgba?\(([^)]+)\)/.exec(str || '');
    if (!m) return null;
    var p = m[1].split(/[ ,\/]+/).filter(Boolean).map(parseFloat);
    return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 };
  }
  function lum(c) {
    var f = function (v) { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
    return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b);
  }
  // Compoe as camadas semitransparentes ate achar um fundo opaco (antes, rgba(.., .05) contava como fundo solido).
  function fundo(el) {
    var camadas = [];
    for (var n = el; n && n.nodeType === 1; n = n.parentElement) {
      var c = rgba(getComputedStyle(n).backgroundColor);
      if (c && c.a > 0) { camadas.push(c); if (c.a >= 1) break; }
    }
    var base = camadas.length && camadas[camadas.length - 1].a >= 1 ? camadas.pop() : { r: 255, g: 255, b: 255, a: 1, assumido: true };
    var out = { r: base.r, g: base.g, b: base.b, a: 1, assumido: base.assumido };
    for (var i = camadas.length - 1; i >= 0; i--) {
      var k = camadas[i];
      out.r = k.r * k.a + out.r * (1 - k.a); out.g = k.g * k.a + out.g * (1 - k.a); out.b = k.b * k.a + out.b * (1 - k.a);
    }
    return out;
  }
  function nome(el) {
    var t = (el.innerText || el.textContent || '').trim();
    if (t) return t;
    if ((el.getAttribute('aria-label') || '').trim()) return 'x';
    if ((el.getAttribute('title') || '').trim()) return 'x';
    if (el.tagName === 'INPUT' && ((el.value || '').trim() || (el.placeholder || '').trim())) return 'x';
    var lb = el.getAttribute('aria-labelledby');
    if (lb && document.getElementById(lb)) return 'x';
    var im = el.querySelector('img[alt]:not([alt=""]), svg title');
    return im ? 'x' : '';
  }
  var out = { alvos_pequenos: [], textos_pequenos: [], sem_nome: [], contraste_baixo: [] };
  var inter = document.querySelectorAll('button, a, input, [role=button], select, textarea');
  Array.prototype.forEach.call(inter, function (el) {
    if (el.closest(IGN) || (el.tagName === 'INPUT' && el.type === 'hidden')) return;
    var r = visivel(el);
    if (!r) return;
    if (r.width < 44 || r.height < 44)
      out.alvos_pequenos.push({ el: desc(el), w: Math.round(r.width), h: Math.round(r.height), texto: (el.innerText || el.value || '').trim().slice(0, 30) });
    if ((el.tagName === 'BUTTON' || el.getAttribute('role') === 'button') && !nome(el))
      out.sem_nome.push({ el: desc(el), w: Math.round(r.width), h: Math.round(r.height) });
  });
  var todos = document.body ? document.body.querySelectorAll('*') : [];
  Array.prototype.forEach.call(todos, function (el) {
    if (/^(SCRIPT|STYLE|NOSCRIPT|SVG|PATH)$/i.test(el.tagName) || el.closest(IGN)) return;
    var tem = false, txt = '';
    for (var i = 0; i < el.childNodes.length; i++) {
      var nd = el.childNodes[i];
      if (nd.nodeType === 3 && nd.nodeValue.trim()) { tem = true; txt += nd.nodeValue.trim() + ' '; }
    }
    if (!tem) return;
    var r = visivel(el);
    if (!r) return;
    var cs = getComputedStyle(el), fs = parseFloat(cs.fontSize);
    txt = txt.trim().slice(0, 40);
    if (fs < 14) out.textos_pequenos.push({ el: desc(el), px: Math.round(fs * 10) / 10, texto: txt });
    if (fs < 18) {
      var fg = rgba(cs.color), bg = fundo(el);
      if (!fg) return;
      var a = fg.a == null ? 1 : fg.a;
      var f2 = { r: fg.r * a + bg.r * (1 - a), g: fg.g * a + bg.g * (1 - a), b: fg.b * a + bg.b * (1 - a) };
      var l1 = lum(f2), l2 = lum(bg), hi = Math.max(l1, l2), lo = Math.min(l1, l2);
      var ratio = (hi + 0.05) / (lo + 0.05);
      if (ratio < 4.5)
        out.contraste_baixo.push({ el: desc(el), razao: Math.round(ratio * 100) / 100, px: Math.round(fs * 10) / 10, texto: txt,
          aproximado: true, fundo_assumido_branco: !!bg.assumido });
    }
  });
  return JSON.stringify(out);
})()
"""

# (nome, JS que abre, JS que fecha). Cada abertura devolve true se achou o gatilho.
CLICK = "(function(s){var e=document.querySelector(s);if(!e)return false;e.click();return true;})(%s)"
TELAS = [
    ("inicial", "true"),
    ("gaveta_apps", CLICK % json.dumps("#hl-dock-drawer")),
    ("ajustes", CLICK % json.dumps("#configure")),
    ("conversa", CLICK % json.dumps("#talk")),
    ("painel_carro", CLICK % json.dumps(".hl-dock-car")),
    ("teclado", "(function(){var e=document.querySelector('#nav-dest');if(!e)return false;e.focus();"
                "if(window.harumiKeyboard&&harumiKeyboard.open){try{harumiKeyboard.open(e);}catch(x){}}return true;})()"),
]
FECHAR = """(function(){
  try { if (window.harumiShell && harumiShell.closeAll) harumiShell.closeAll(); } catch (e) {}
  ['#hl-drawer', '#hl-carview'].forEach(function (s) { var e = document.querySelector(s); if (e) e.style.display = 'none'; });
  try { if (window.harumiKeyboard && harumiKeyboard.close) harumiKeyboard.close(); } catch (e) {}
  if (document.activeElement && document.activeElement.blur) document.activeElement.blur();
  return true;
})()"""
# Reexibe o que a fechada acima ocultou, para a tela seguinte poder abrir de novo.
REEXIBIR = """(function(){
  ['#hl-drawer', '#hl-carview'].forEach(function (s) { var e = document.querySelector(s); if (e) e.style.display = ''; });
  return true;
})()"""


def avaliar(ws, expr):
    r = ws.call("Runtime.evaluate", {"expression": expr, "returnByValue": True, "awaitPromise": True})
    res = r.get("result", {})
    if "exceptionDetails" in res:
        raise RuntimeError(res["exceptionDetails"].get("text", "erro JS") + " " +
                           str(res["exceptionDetails"].get("exception", {}).get("description", ""))[:200])
    return res.get("result", {}).get("value")


def cortar(lista):
    return lista[:LIMITE]


def auditar_telas(ws, avisos):
    telas, totais = {}, {}
    for nome, abrir in TELAS:
        try:
            achou = avaliar(ws, abrir)
            if not achou:
                avisos.append("tela '%s': gatilho nao encontrado, medida mesmo assim" % nome)
            time.sleep(1)
            dados = json.loads(avaliar(ws, JS_MEDIR))
        except Exception as e:  # uma tela falhar nao derruba o resto
            avisos.append("tela '%s': falhou (%s)" % (nome, e))
            dados = {"alvos_pequenos": [], "textos_pequenos": [], "sem_nome": [], "contraste_baixo": []}
        totais[nome] = {k: len(v) for k, v in dados.items()}
        telas[nome] = {k: cortar(v) for k, v in dados.items()}
        telas[nome]["total"] = totais[nome]
        try:
            avaliar(ws, FECHAR)
            time.sleep(0.4)
            avaliar(ws, REEXIBIR)
        except Exception as e:
            avisos.append("fechar apos '%s': %s" % (nome, e))
    return telas, totais


def escutar_console(ws):
    console, csp = [], []
    ws.call("Runtime.enable")
    ws.call("Log.enable")
    ws.call("Page.enable")
    ws.send("Page.reload", {"ignoreCache": True})
    ws.s.settimeout(1)
    fim = time.time() + ESCUTA_S
    while time.time() < fim:
        try:
            m = ws.recv()
        except socket.timeout:
            continue
        except EOFError:
            break
        met, p = m.get("method"), m.get("params", {})
        txt = None
        if met == "Runtime.exceptionThrown":
            d = p.get("exceptionDetails", {})
            txt = "excecao: " + str(d.get("exception", {}).get("description") or d.get("text"))[:300]
            txt += " (%s:%s)" % (d.get("url", ""), d.get("lineNumber", ""))
        elif met == "Log.entryAdded":
            e = p.get("entry", {})
            txt = "[%s] %s (%s)" % (e.get("level"), e.get("text", "")[:300], e.get("url", ""))
            if e.get("level") != "error" and "Content Security Policy" not in txt:
                txt = None
        elif met == "Runtime.consoleAPICalled" and p.get("type") == "error":
            txt = "console.error: " + " ".join(str(a.get("value", a.get("description", ""))) for a in p.get("args", []))[:300]
        if txt:
            (csp if "Content Security Policy" in txt else console).append(txt)
    ws.s.settimeout(20)
    time.sleep(0.5)
    return console, csp


def main():
    avisos = []
    ws = cdp.WS(cdp.target())
    try:
        console, csp = escutar_console(ws)
    except Exception as e:
        console, csp = [], []
        avisos.append("escuta de console falhou: %s" % e)
    try:
        telas, totais = auditar_telas(ws, avisos)
    except Exception as e:
        telas, totais = {}, {}
        avisos.append("auditoria de telas falhou: %s" % e)
    soma = {}
    for t in totais.values():
        for k, v in t.items():
            soma[k] = soma.get(k, 0) + v
    resumo = {
        "por_tela": totais,
        "soma": soma,
        "console_total": len(console),
        "csp_total": len(csp),
        "limite_por_lista": LIMITE,
        "contraste": "aproximado (cor do texto sobre a primeira cor de fundo nao transparente dos ancestrais; branco se nenhuma)",
        "avisos": avisos,
    }
    print(json.dumps({"telas": telas, "console": cortar(console), "csp": cortar(csp), "resumo": resumo},
                     ensure_ascii=False, indent=1))


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        print(json.dumps({"telas": {}, "console": [], "csp": [], "resumo": {"avisos": [str(e)]}}, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"telas": {}, "console": [], "csp": [], "resumo": {"avisos": ["erro: %s" % e]}}, ensure_ascii=False))
    sys.exit(0)
