#!/usr/bin/env python3
"""Teste de uso da Harumi OS no Orange Pi, como um motorista exigente: cada tarefa usa os mesmos botoes e o teclado
na tela que o usuario tocaria, mede passos e tempo e salva capturas em /tmp/ux-*.png. Saida em JSON.
Uso (na placa, na pasta ~/harumi):  python3 ux_walkthrough.py
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdp  # noqa: E402

RESULTS = []


def ui():
    return cdp.WS(cdp.target())


def ev(js):
    w = ui()
    r = w.call("Runtime.evaluate", {"expression": js, "returnByValue": True, "awaitPromise": True})
    return r.get("result", {}).get("result", {}).get("value")


def shot(name):
    w = ui()
    r = w.call("Page.captureScreenshot", {"format": "png"})
    import base64
    open(f"/tmp/ux-{name}.png", "wb").write(base64.b64decode(r["result"]["data"]))


TAP = """(sel => { const e = typeof sel === 'string' ? document.querySelector(sel) : sel; if (!e) return false; e.click(); return true; })"""
KEYS = """(text => { const k = t => [...document.querySelectorAll('#hl-kb .hl-kb-key')].find(b => b.textContent === t);
  for (const ch of text) { const b = k(ch === ' ' ? 'espaço' : ch); if (!b) return 'tecla ausente: ' + ch;
    b.dispatchEvent(new PointerEvent('pointerdown', {bubbles: true, cancelable: true})); } return 'ok'; })"""


def task(name, steps):
    t0 = time.time()
    notes, ok = [], True
    for i, (label, js, wait) in enumerate(steps, 1):
        try:
            v = ev(js)
        except Exception as e:  # passo quebrou
            v = f"erro: {e}"
        notes.append(f"{i}. {label}: {v}")
        if v is False or (isinstance(v, str) and v.startswith(("erro", "tecla ausente", "falhou"))):
            ok = False
        time.sleep(wait)
    RESULTS.append({"tarefa": name, "ok": ok, "toques": len(steps), "segundos": round(time.time() - t0, 1), "passos": notes})


def wait_ready(limit=45):
    """Espera a tela ficar pronta (scripts carregados e mapa desenhado) em vez de um tempo fixo."""
    time.sleep(3)
    t0 = time.time()
    while time.time() - t0 < limit:
        try:
            if ev("document.readyState==='complete' && !!window.harumiKeyboard && !!window.harumiEmbed && "
                  "!!document.querySelector('#route-canvas canvas, #route-canvas .leaflet-tile-loaded')"):
                break
        except Exception:  # pagina recarregando
            pass
        time.sleep(1)
    time.sleep(4)  # o mapa termina de se ajustar ao tamanho


def home():
    ev("(()=>{ if (window.harumiEmbed) window.harumiEmbed.close(); if (window.harumiKeyboard) window.harumiKeyboard.close();"
       " if (window.harumiShell) window.harumiShell.closeAll(); const c=document.getElementById('hl-carview'); if(c) c.hidden=true;"
       " const d=document.getElementById('hl-drawer'); if(d) d.hidden=true;"
       " const gr=document.getElementById('hl-greet'); if(gr) gr.hidden=true; return 1 })()")  # saudacao da partida
    time.sleep(1)


def main():
    ev("location.reload(), 1")
    wait_ready()
    shot("0-inicio")

    home()
    task("Buscar destino e iniciar navegacao (Catedral de Londrina)", [
        ("tocar no card Navegar", TAP + "('.hl-navcard-search')", 1),
        ("teclado abriu", "!document.getElementById('hl-kb').hidden || 'falhou: teclado fechado'", 0),
        ("digitar 'catedral londrina'", KEYS + "('catedral londrina')", 0.5),
        ("tocar OK", "(()=>{[...document.querySelectorAll('#hl-kb .hl-kb-key')].find(b=>b.textContent==='OK').dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,cancelable:true}));return 'ok'})()", 6),
        ("resultados na tela", "(()=>{const r=document.querySelectorAll('#nav-results .nav-result');return r.length? r.length+' resultados; 1o: '+r[0].innerText.replace(/\\n/g,' ').slice(0,70):'falhou: nenhum resultado'})()", 0),
        ("tocar no 1o resultado", TAP + "('#nav-results .nav-result')", 8),
        ("previa da rota (ou, sem GPS, a oferta de rota a partir de Casa)", "(()=>{const p=document.getElementById('route-result');if(p&&!p.hidden)return p.innerText.replace(/\\n/g,' ').slice(0,90);const b=document.querySelector('.hl-fromhome');return b&&getComputedStyle(b).display!=='none'?'sem GPS: botao Ver rota a partir de Casa na tela':'falhou: sem previa e sem oferta'})()", 0),
    ])
    shot("1-rota")

    home()
    task("Perguntar a Harumi: qual oleo do cambio?", [
        ("tocar Harumi no dock", TAP + "('#hl-dock [data-dock=harumi]')", 1.5),
        ("painel de conversa aberto", "!document.getElementById('assistant').hidden || 'falhou'", 0),
        ("tocar no campo de texto", "(()=>{const i=document.getElementById('question');if(!i)return 'falhou: sem campo';i.focus();i.dispatchEvent(new PointerEvent('pointerup',{bubbles:true}));return i.id})()", 1),
        ("teclado abriu", "!document.getElementById('hl-kb').hidden || 'falhou: teclado fechado'", 0),
        ("digitar a pergunta", KEYS + "('qual oleo do cambio')", 0.5),
        ("tocar OK", "(()=>{[...document.querySelectorAll('#hl-kb .hl-kb-key')].find(b=>b.textContent==='OK').dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,cancelable:true}));return 'ok'})()", 5),
        ("resposta", "(()=>{const p=[...document.querySelectorAll('#conversation p')].pop();return p? p.innerText.replace(/\\n/g,' ').slice(0,120):'falhou'})()", 0),
    ])
    shot("2-harumi")

    home()
    task("YouTube: abrir, buscar 'subaru impreza', tela cheia, fechar", [
        ("tocar YouTube no dock", TAP + "('#hl-dock [data-dock=video]')", 12),
        ("card aberto", "(window.harumiEmbed && window.harumiEmbed.current()) || 'falhou'", 0),
        ("tocar Tela cheia", "(()=>{const b=[...document.querySelectorAll('#hl-embed .hl-embed-btn')].find(b=>b.textContent==='Tela cheia');if(!b)return 'falhou';b.click();return 'ok'})()", 1),
        ("tocar Teclado", "(()=>{const b=[...document.querySelectorAll('#hl-embed .hl-embed-btn')].find(b=>b.textContent==='Teclado');if(!b)return 'falhou';b.click();return !document.getElementById('hl-kb').hidden||'falhou'})()", 1),
    ])
    task("YouTube (cont.): digitar e buscar", [
        ("digitar", KEYS + "('subaru impreza')", 0.5),
        ("tocar OK", "(()=>{[...document.querySelectorAll('#hl-kb .hl-kb-key')].find(b=>b.textContent==='OK').dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,cancelable:true}));return 'ok'})()", 6),
    ])
    os.environ["CDP_MATCH"] = "youtube.com"
    try:
        url = ev("location.href")
    finally:
        os.environ["CDP_MATCH"] = "127.0.0.1:8765"
    RESULTS[-1]["passos"].append("3. pagina do YouTube: " + str(url))
    if "search_query=subaru" not in str(url):
        RESULTS[-1]["ok"] = False
    shot("3-youtube")
    task("YouTube (cont.): fechar", [("tocar Fechar", TAP + "('#hl-embed .hl-embed-btn.close')", 1),
                                     ("card fechado", "!(window.harumiEmbed && window.harumiEmbed.current()) || 'falhou'", 0)])

    home()
    task("Aumentar o volume duas vezes", [
        ("ler volume", "document.querySelector('.hl-vol-level').textContent", 0),
        ("tocar +", "(()=>{const b=[...document.querySelectorAll('.hl-vol-btn')].pop();b.click();return 'ok'})()", 1),
        ("tocar +", "(()=>{const b=[...document.querySelectorAll('.hl-vol-btn')].pop();b.click();return 'ok'})()", 1.5),
        ("volume agora", "document.querySelector('.hl-vol-level').textContent", 0),
        ("voltar ao volume anterior", "(()=>{const b=document.querySelector('.hl-vol-btn');b.click();setTimeout(()=>b.click(),600);return 'ok'})()", 2),
    ])

    home()
    task("Achar o ajuste de Internet", [
        ("abrir Apps", TAP + "('#hl-dock-drawer')", 1),
        ("tocar Ajustes", "(()=>{const t=[...document.querySelectorAll('.hl-tile')].find(t=>t.textContent.includes('Ajustes'));if(!t)return 'falhou';t.click();return 'ok'})()", 1),
        ("tocar na busca", "(()=>{const i=document.querySelector('.hl-settings-search input');if(!i)return 'falhou';i.focus();i.dispatchEvent(new PointerEvent('pointerup',{bubbles:true}));return !document.getElementById('hl-kb').hidden||'falhou: teclado fechado'})()", 0.5),
        ("digitar 'internet'", KEYS + "('internet')", 0.5),
        ("linhas visiveis", "[...document.querySelectorAll('#settings .hu-row')].filter(r=>!r.hidden).map(r=>r.innerText.split('\\n')[0]).join(', ') || 'falhou: nada'", 0),
    ])
    shot("4-ajustes")

    home()
    task("Fixar o Claude no dock (e desfazer)", [
        ("abrir Apps", TAP + "('#hl-dock-drawer')", 1),
        ("tocar Editar dock", TAP + "('.hl-drawer-edit')", 0.5),
        ("dock cheio? quantos apps", "document.querySelectorAll('#hl-dock .hl-dock-apps button').length", 0),
        ("tocar Claude", "(()=>{const t=[...document.querySelectorAll('.hl-tile')].find(t=>t.textContent.includes('Claude'));if(!t)return 'falhou';t.click();return 'ok'})()", 0.5),
        ("resultado", "document.querySelector('#hl-dock [data-dock=claude]') ? 'Claude fixado' : (document.getElementById('message').hidden ? 'falhou: sem aviso' : 'aviso: '+document.getElementById('message').textContent)", 0),
        ("desfazer se fixou", "(()=>{if(document.querySelector('#hl-dock [data-dock=claude]')){[...document.querySelectorAll('.hl-tile')].find(t=>t.textContent.includes('Claude')).click()}return 'ok'})()", 0.3),
        ("tocar Concluir", TAP + "('.hl-drawer-edit')", 0.3),
    ])

    home()
    task("Ver o painel do carro", [
        ("tocar no carro (barra)", TAP + "('.hl-dock-car')", 1),
        ("painel aberto", "!document.getElementById('hl-carview').hidden || 'falhou'", 0),
        ("fechar", TAP + "('.hl-carview-close')", 0.5),
    ])
    home()
    run_extensions()
    print(json.dumps(RESULTS, ensure_ascii=False, indent=1))


def run_extensions():
    """Roda todo tools/ux_*.py (menos este e ux_audit.py) que defina run(ev, shot, task); o resultado entra no mesmo JSON."""
    import importlib.util
    import traceback
    here = os.path.dirname(os.path.abspath(__file__))
    for fn in sorted(os.listdir(here)):
        if not (fn.startswith("ux_") and fn.endswith(".py")) or fn in ("ux_walkthrough.py", "ux_audit.py"):
            continue
        try:
            spec = importlib.util.spec_from_file_location("hux_" + fn[:-3], os.path.join(here, fn))
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            if not callable(getattr(mod, "run", None)):
                continue
            extra = mod.run(ev, shot, task)
            if extra is not None:
                RESULTS.append({"extensao": fn, "resultado": extra})
        except Exception as e:  # uma extensao quebrada nao invalida o resto do teste
            RESULTS.append({"extensao": fn, "ok": False, "erro": repr(e), "detalhe": traceback.format_exc()[-600:]})
        home()


if __name__ == "__main__":
    main()
