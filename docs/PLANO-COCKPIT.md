# Plano: navegação cockpit (estilo TomTom, identidade Harumi)

Plano do consultor, 03/11/2026. É a referência dos executores.

## Layout (1024x600)

```
section#road-map.cockpit            fixed; inset:0; z-index:8; background:#1b1b21 (sem borda/padding/moldura)
├ div#route-canvas                  absolute; inset:0  (MapLibre ou Leaflet)
├ div#route-map-network             pill aviso de rede, topo central, hidden
├ header.ck-top                     absolute; top:0; h:36px; padding:0 16px; gradiente rgba(27,27,33,.85)->transparent
│   ├ button#close-road-map.ck-icon "Início" (ícone casa; área tocável >=56)   <- mantém ID
│   ├ span#ck-engine "3D"/"2D" (12px muted; harumiNav.engine())
│   └ span.ck-right: span#ck-net (espelha #network-short via MutationObserver se existir) · time#ck-clock HH:MM (setInterval 30s)
├ aside.ck-left                     absolute; left:16; top:48; bottom:96; width:340; flex column gap 10; pointer-events:none (filhos auto)
│   [planejar]
│   ├ form#nav-form.ck-card.ck-search      lupa + input#nav-dest "Para onde vamos?" + button#nav-search só ícone 56x56
│   │   ├ p#nav-lock (pill âmbar, hidden)
│   │   └ p#nav-search-status (13px muted; vazio por padrão)
│   ├ div#nav-results.ck-card.ck-list      lista numerada: <button class="nav-result"><i>1</i><strong>nome</strong><span>detalhe</span><em>12 km</em></button>
│   ├ button#ck-cities-toggle.ck-chip "Entre duas cidades" aria-expanded   (substitui o details/summary)
│   ├ form#route-form.ck-card.route-cities hidden; #route-from, #route-to, #swap-route (ícone), #calculate-route "Traçar"
│   ├ p#route-status (13px; só com texto útil)
│   └ div#route-result.ck-card.ck-preview  hidden; strong#route-distance · strong#route-duration · strong#route-arrive ("chegada 14:32" = agora+duração) · p#route-endpoints · button#route-start "Iniciar navegação" (acento; disabled sem GPS + "Sem sinal de GPS") · button#route-external "Outro app" · button#fit-route (ícone)
│   [navegar]  (#nav-hud vira contêiner lógico; filhos ficam nas colunas)
│   ├ div#nav-banner.ck-card  (#nav-arrow 88x88 acento, #nav-dist 48px, #nav-street 20px)
│   └ div#nav-next.ck-pill · div#nav-lanes.ck-card · div#nav-gps.ck-pill-warn · div#nav-msg.ck-pill-warn (+#nav-retry)
├ aside.ck-right                    absolute; right:16; top:48; bottom:96; width:300; mesma pilha
│   [navegar]
│   ├ div#ck-trip.ck-card    strong#nav-eta 36px "chegada" + linha #nav-rem · #nav-time + div#nav-progress (barra 4px)
│   ├ div#ck-speed.ck-card   strong#nav-speed 44px + "km/h" (sem limite de velocidade: não temos o dado)
│   └ div#ck-media.ck-card   "Som do carro" / "Controles por Bluetooth/rádio" + 3 botões 56x56 data-action media.previous / media.playpause / media.next
│   [planejar]
│   ├ div#ck-media (igual)
│   └ div#ck-assist.ck-card  "Harumi" + botão 56px "Falar" data-action="assistant.listen"
├ div.ck-fab                        absolute; right:16; bottom:112; column gap 10
│   ├ .m3-zoom (cápsula vertical 56x116 + / −; criada pelo map3d.js; só reposicionar), no 2D, o zoom do Leaflet no mesmo lugar
│   └ button#nav-recenter.ck-fab-btn (bússola; hidden quando following)
└ nav.ck-tabs                       absolute; left:0; right:0; bottom:0; h:84px
    ├ canto esq: button#nav-stop "Encerrar" (pill 56px, fundo #6b4a5e, texto #f0eaf0; só em .nav-on)
    ├ abas: [home] "Início" (→ close) · [nav] "Navegar" (ativa) · data-action="apps.open.music" "Música" · data-action="assistant.listen" "Harumi" · button#ck-tab-apps "Apps" (→ #open-apps.click())
    └ canto dir: p#nav-credit (crédito do motor + "Rotas: OSRM"; sempre visível, 11px) · button.nav-replay-btn (só debug)
```

**Telas menores:**
- **`@media (max-width:900px)`:** colunas 292/252; `.ck-top` 32px; abas 72px; `#ck-media` escondido em `.nav-on`; `#nav-dist` 40px.
- **`@media (max-width:600px)` (retrato):**
  - `.ck-left` em `left:12; right:12; top:44`.
  - `.ck-right` vira faixa horizontal em `bottom:92; left:12; right:12`, em linha, só com `#ck-trip` e `#ck-speed`.
  - `.ck-fab` em `bottom:200`; abas 64px.
  - `#nav-results` mostra no máximo 4 itens, com rolagem.

**Tokens (em `#road-map{}`):**
- `--ck-glass:rgba(43,36,50,.86)`
- `--ck-glass-strong:rgba(43,36,50,.94)`
- `--ck-stroke:rgba(240,234,240,.10)`
- `--ck-stroke-hi:rgba(240,234,240,.18)`
- `--ck-text:#f0eaf0`
- `--ck-muted:#b9a9bb`
- `--ck-accent:#d2a0bd`
- `--ck-accent-ink:#2a1e2b`
- `--ck-glow:0 0 14px rgba(210,160,189,.55)`
- `--ck-shadow:0 8px 24px rgba(16,10,18,.45)`
- `--ck-r:16px`
- `--ck-r-sm:12px`
- `--ck-tab-h:84px`
- `font-family:"Segoe UI",Roboto,"Noto Sans",system-ui,sans-serif`

**Cartão:**
- `background:var(--ck-glass)`
- `border:1px solid var(--ck-stroke)`
- `border-radius:16px`
- `box-shadow:var(--ck-shadow), inset 0 1px 0 var(--ck-stroke-hi)`
- `padding:14px 16px`

**Blur:** sem `backdrop-filter` por padrão. `.ck-blur .ck-card{backdrop-filter:blur(14px)}` fica como opção, a decidir depois de medir o FPS.

**Abas:**
- Ativa: ícone `#f0eaf0`, sublinhado de 28x3px `#d2a0bd`, com `box-shadow:0 0 12px rgba(210,160,189,.7)`.
- Inativa: `#a391a5`.

**Tipografia:** rótulos com 13px em `--ck-muted`; valores de 28 a 48px, peso 600; nada em caixa alta.

**Ícones:** em `<svg>` inline com `<symbol>` (padrão já usado em `#m-*`): casa, navegar, música, harumi, apps, bússola, lupa, inverter, anterior, play/pause, próximo. Sem download.

## Mapa 3D

**map3d.js:**
- `NAV_PITCH 66` e `maxPitch 72` (confirmar o limite no `.mjs`).
- `follow` com `padding top: H*0.40`.
- Novo `frame(lat,lon,zoom=13,pitch=30)` para o planejador.
- `fitBounds` aceita `padding` como objeto `{top:60,left:380,right:40,bottom:110}`.
- Carro em SVG de 84px, com `stroke #f6eef4` de 3px e brilho (`.m3-car i`) de 150px `rgba(232,170,208,.45)`.
- `.m3-fog` com 26% da altura, deixando o céu do estilo trabalhar.

**map-style-harumi.json:**
- **Luz:** `light` = `{"anchor":"map","color":"#f3dcea","intensity":0.55,"position":[1.4,200,40]}`.
- **Céu:** `sky` = `{"sky-color":"#2b2333","horizon-color":"#6b4b66","fog-color":"#3b2e3d","sky-horizon-blend":0.5,"horizon-fog-blend":0.6,"fog-ground-blend":0.5}`.
- **Fundo:** `background` `#211d26`.
- **Prédios (`building-3d`):**
  - `fill-extrusion-color` interpolado por `render_height`: 0 `#5c4d62`, 20 `#7a6880`, 50 `#978499`, 120 `#b49fb8`.
  - Opacidade 0.78, `vertical-gradient` true, `minzoom` 14.
- **Vias:**
  - minor `#332c38`; tertiary/secondary `#3d3442`; primary/trunk/motorway `#463b4b`; casings `#1a171e`.
- **Faixas pintadas (`road-lane-dash`):**
  - Camada nova acima dos preenchimentos, `minzoom` 15.
  - Filtro: classe em `["primary","trunk","motorway","secondary"]`.
  - `line-color rgba(240,234,240,.32)`.
  - `line-width` 15:1, 17:1.8, 18:2.4; `dasharray [3,4]`.
- **Rota:**
  - `glow` `#e39cc9`: largura 13:26 / 16:56 / 18:72; blur 13:12 / 16:26 / 18:34; opacidade .85.
  - `casing` `#5a3f55`: 13:14 / 16:24 / 18:30.
  - `line` `#f1c4dd`: 13:8 / 16:17 / 18:22.
  - `done` `#8a7488`: mesma largura da linha, opacidade .9.
- **Rótulos:** se o pitch 66 poluir, `label-road-minor` com `minzoom` 16.5.

## Planejador

- **`open()`:**
  - Com `usableFix()`: `frame(lastFix,13,30)` no 3D, ou `setView([lat,lon],13)` no 2D.
  - Sem fix: Brasil em z4 (não inventar posição).
  - `stopNav()` faz o mesmo.
  - Limpa `#nav-search-status` ao abrir.
- **Busca:** resultados numerados, com distância em linha reta a partir de `lastFix` (haversine do Core). Sem fix, a distância é omitida.
- **Sugestões com o campo vazio:**
  - Não existem "recentes".
  - Opcional: 5 chips com as cidades de `cities-data.js` mais próximas da posição, só se houver fix.
- **Rota entre cidades:**
  - `fitBounds` com padding `left:380`.
  - `#route-arrive` = agora + duração.
  - `#route-start` → `startNav({name,lat,lon})`.
- **Toggle de cidades:** `#ck-cities-toggle` alterna `hidden` do `#route-form`. `openCities()` passa a usar esse toggle.
- **Créditos:** remover `.route-foot`; o crédito fica em `#nav-credit`.

## Não fazer

- `backdrop-filter` por padrão.
- Pitch acima de 72.
- Cartões de clima, agenda, telefone ou ar-condicionado; capa ou título de música; limite de velocidade. Não há dados para nenhum deles.
- Trocar IDs.
- Abrir `#assistant` por cima do mapa.
- Reescrever `road-map.js` inteiro: não mexer na lógica de guia e recálculo.
- Fazer downloads.
