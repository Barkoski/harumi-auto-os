(function () {
  'use strict';
  var DURACAO_MS = 10000;

  function gl(tipo) {
    try { return document.createElement('canvas').getContext(tipo); } catch (e) { return null; }
  }

  function infoGl() {
    var r = { webgl2: false, webgl: false, maxTextureSize: null, renderer: null, vendor: null };
    var g2 = gl('webgl2'), g1 = gl('webgl');
    r.webgl2 = !!g2; r.webgl = !!g1;
    var g = g2 || g1;
    if (g) {
      r.maxTextureSize = g.getParameter(g.MAX_TEXTURE_SIZE);
      var ext = g.getExtension('WEBGL_debug_renderer_info');
      if (ext) {
        r.renderer = g.getParameter(ext.UNMASKED_RENDERER_WEBGL);
        r.vendor = g.getParameter(ext.UNMASKED_VENDOR_WEBGL);
      }
    }
    return r;
  }

  function medirFps() {
    return new Promise(function (resolve) {
      var palco = document.createElement('div');
      palco.style.position = 'fixed'; palco.style.left = '0'; palco.style.top = '0';
      palco.style.width = '1450px'; palco.style.height = '870px';
      palco.style.overflow = 'hidden'; palco.style.zIndex = '-1';
      var alvo = document.createElement('div');
      alvo.style.width = '1450px'; alvo.style.height = '870px'; alvo.style.position = 'relative';
      alvo.style.willChange = 'transform';
      for (var i = 0; i < 200; i++) {
        var t = document.createElement('div');
        t.style.position = 'absolute';
        t.style.width = '145px'; t.style.height = '87px';
        t.style.left = (i % 10) * 145 + 'px'; t.style.top = Math.floor(i / 10) * 43 + 'px';
        t.style.background = 'hsl(' + (i * 37 % 360) + ',45%,60%)';
        t.style.border = '1px solid rgba(0,0,0,.2)';
        t.style.boxSizing = 'border-box';
        t.textContent = 'tile ' + i;
        alvo.appendChild(t);
      }
      palco.appendChild(alvo); document.body.appendChild(palco);
      var tempos = [], ini = null, ant = null;
      function quadro(ts) {
        if (ini === null) ini = ts;
        if (ant !== null) tempos.push(ts - ant);
        ant = ts;
        alvo.style.transform = 'rotate(' + (((ts - ini) / 20) % 360) + 'deg)';
        if (ts - ini < DURACAO_MS) { requestAnimationFrame(quadro); return; }
        palco.remove();
        var total = tempos.reduce(function (a, b) { return a + b; }, 0);
        var fps = tempos.length ? 1000 * tempos.length / total : 0;
        // p5 = FPS do pior 5% dos quadros (percentil 95 do tempo de quadro)
        var ord = tempos.slice().sort(function (a, b) { return a - b; });
        var p95 = ord.length ? ord[Math.min(ord.length - 1, Math.floor(ord.length * 0.95))] : 0;
        resolve({
          fpsMedio: +fps.toFixed(1),
          fpsP5: p95 ? +(1000 / p95).toFixed(1) : 0,
          quadros: tempos.length,
          quadroMaxMs: ord.length ? +ord[ord.length - 1].toFixed(1) : 0
        });
      }
      requestAnimationFrame(quadro);
    });
  }

  function coletar() {
    var ua = navigator.userAgent;
    var m = /Chrome\/(\d+)/.exec(ua);
    var chrome = m ? parseInt(m[1], 10) : null;
    var g = infoGl();
    var r = {
      userAgent: ua, chrome: chrome,
      gl: g,
      devicePixelRatio: window.devicePixelRatio,
      screen: { w: screen.width, h: screen.height },
      janela: { w: window.innerWidth, h: window.innerHeight },
      hardwareConcurrency: navigator.hardwareConcurrency || null,
      deviceMemory: navigator.deviceMemory || null,
      memoriaJs: performance.memory ? {
        usado: performance.memory.usedJSHeapSize,
        total: performance.memory.totalJSHeapSize,
        limite: performance.memory.jsHeapSizeLimit
      } : null
    };
    return medirFps().then(function (f) {
      r.fps = f;
      var soft = /swiftshader|llvmpipe|software/i.test((g.renderer || '') + ' ' + (g.vendor || ''));
      r.rendererSoftware = soft;
      r.maplibreViavel = !!(g.webgl2 && !soft && chrome !== null && chrome >= 90 && f.fpsMedio >= 45);
      return r;
    });
  }

  window.harumiGpuProbe = coletar().then(function (r) {
    var json = JSON.stringify(r);
    var pre = document.getElementById('out');
    if (pre) pre.textContent = JSON.stringify(r, null, 2);
    console.log('HARUMI_GPU ' + json);
    return r;
  });
})();
