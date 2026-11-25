# Plano: sistema inteiro no idioma cockpit (identidade Harumi)

Plano do consultor, 04/11/2026. É a referência dos executores. O cockpit (`#road-map`) é o modelo; ver docs/PLANO-COCKPIT.md.

## Diagnóstico (fatos)

- **CSS em uso:** `index.html` carrega style.css, atlas.css, leaflet/maplibre, road-map.css, apps-catalog.css e launcher.css.
  - harumi-pink.css, large-buttons.css, original.css e retro.css estão mortos: nenhum está vinculado.
  - O tema real é o launcher.css sobrescrevendo os tokens azuis do style.css.
- **Tokens do cockpit:** os `--ck-*` estão escopados em `#road-map{}` no road-map.css. As classes `.ck-card`, `.ck-tab`, `.ck-chip`, `.ck-talk` e `.ck-media-btns` não têm prefixo.
- **Telefone:** "Telefone" é `data-action="catalog.open" data-module="bluetooth"`, o app OEM. Não há telefonia própria.
- **Barra nativa:** a barra "Interface de fábrica" é nativa (MainActivity:58). Não tocar.
- **Navegação fora do cockpit:** `road-map.js close()` chama `stopNav()`. Portanto não existe destino em curso fora do cockpit, e a Home não mostra ETA.
- **Testes:** test_ui.py, test_launcher.py e test_apps_catalog.py provavelmente já estão desatualizados. Rodar a linha de base antes.
- **Funções que o nativo chama no JS:** manter todas.
  - `harumiUpdate`, com as chaves `wake`, `animation`, `NAV`, `MUSIC`, `CAMERA360`, `assistantStatus`, `assistantBusy`, `diagnostics`, `connectivity` e `device`.
  - `harumiLauncherUpdate` e `harumiLauncherRefresh`.
  - `harumiAppsUpdate`, `harumiOpenAssistant`, `harumiBack` e `harumiVisibility`.
  - `harumiRoadMap.open`, `harumiRoadMap.plan` e `harumiRoadMap.navigateTo`.

## Estratégia

1. **`harumi-ui.css` (novo)**, carregado antes de road-map.css.
   - Tokens `--ck-*` em `:root`, com os mesmos valores do cockpit.
   - Componentes compartilhados: `.ck-card`, `.ck-ico`, `.ck-chip`, `.ck-talk`, `.hu-tabs`, `.hu-screen`, `.hu-head`, `.hu-btn`, `.hu-icon-btn` e `.hu-chips`.
   - road-map.css não muda.
2. **Barra de abas global `nav#hu-tabs`:** fixed, bottom 0, altura `var(--ck-tab-h)` = 84px, z-index 7.
   - Abas: Início, Navegar, Música, Harumi e Apps, com os mesmos símbolos e estilo do cockpit.
   - O cockpit (z-index 8, inset 0) cobre essa barra.
   - As outras telas: `.hu-screen{position:fixed;top:0;left:0;right:0;bottom:var(--ck-tab-h);z-index:6}`, full-bleed e sem borda.
3. **Home:** cartões de vidro sobre gradiente CSS estático. Nada de mapa ao vivo.
4. **`harumi-shell.js`:**
   - Aba ativa: MutationObserver no `hidden` das seções.
   - Espelha `#assistant-status` em `#hu-harumi-status`.
   - `closeAll()`.
   - Copia `#harumi-actor[data-animation]` para `#assistant[data-voice]`.
5. **Telas secundárias:**
   - Cabeçalho de 56px: título de 22px e ações em botões de 56px à direita.
   - Conteúdo em cartões.
   - Texto explicativo em no máximo uma linha de 13px em `--ck-muted`.

## Tokens (harumi-ui.css, :root)

`--ck-glass:rgba(43,36,50,.86); --ck-glass-strong:rgba(43,36,50,.94); --ck-stroke:rgba(240,234,240,.10); --ck-stroke-hi:rgba(240,234,240,.18); --ck-text:#f0eaf0; --ck-muted:#b9a9bb; --ck-accent:#d2a0bd; --ck-accent-ink:#2a1e2b; --ck-glow:0 0 14px rgba(210,160,189,.55); --ck-shadow:0 8px 24px rgba(16,10,18,.45); --ck-r:16px; --ck-r-sm:12px; --ck-tab-h:84px; --ck-warn-bg:#5a4634; --ck-warn-text:#ffe9c9; --hu-bg:#1b1b21; --hu-bg-glow1:rgba(98,70,94,.35); --hu-bg-glow2:rgba(118,81,110,.30)`

- **body:** `margin:0; background:var(--hu-bg); color:var(--ck-text); font:16px "Segoe UI",Roboto,"Noto Sans",system-ui,sans-serif`.
- **Fundo da Home:** `radial-gradient(ellipse at 78% -10%,var(--hu-bg-glow1),transparent 55%), radial-gradient(ellipse at 15% 115%,var(--hu-bg-glow2),transparent 60%), var(--hu-bg)`.
- **Telas menores:** `@media(max-width:900px){--ck-tab-h:72px}` e `@media(max-width:600px){--ck-tab-h:64px}`.
- **Foco:** `:focus-visible{outline:3px solid var(--ck-accent);outline-offset:2px}`.
- **Movimento reduzido:** com `prefers-reduced-motion: reduce`, `animation:none` e `transition:none`.
- **Sem `backdrop-filter`.**

## Sprite

- Mover o `<svg hidden>` com todos os `<symbol>` `m-*` e `ck-*` para o início do `<body>`, fora de `#road-map`.
- Acrescentar símbolos de linha 24x24 com stroke 2: `ck-phone`, `ck-camera`, `ck-wifi`, `ck-settings`, `ck-globe`, `ck-car`, `ck-chat`, `ck-refresh`, `ck-close`, `ck-chevron` e `ck-bt`.
- A Home deixa de usar os ícones coloridos de `icons/`. Eles continuam valendo para os ícones reais de apps.

## Home: `section#home.hu-home`

A seção fica em `position:fixed; inset:0 0 var(--ck-tab-h) 0`.

```
header.hu-top (h 36; padding 0 16; 13px --ck-muted)
  span.hu-brand "Harumi" (16px 600 --ck-text) + span "Auto OS"
  span#device (direita; truncado)
  button#configure.hu-icon-btn aria-label="Ajustes" (56x56, ck-settings)        <- ID mantido
main.hu-grid (padding 12 16; grid 3 colunas 1fr; rows 176px 1fr; gap 12)
  article#hu-clock.ck-card (col 1): time#clock 64px/600 tabular; span#date 15px muted; span#network-short 13px muted (máx 2 linhas)
  article#hu-go.ck-card (col 2/4): p.hu-label "Para onde vamos?"; button#home-road-map.hu-search (h56, lupa + "Buscar endereço, lugar ou cidade" 19px muted, borda --ck-stroke-hi, raio 28); div.hu-chips: button#hu-cities.ck-chip "Entre duas cidades" · button#open-atlas.ck-chip "Explorar o Brasil" (ck-globe)
  article#hu-harumi.ck-card (col 1): div#home-avatar-slot (96x132; avatar.js move #harumi-actor) ; strong "Harumi" 18px; span#hu-harumi-status 13px muted ; button#voice-home.ck-talk "Falar" (ck-mic 56) · button#talk.hu-btn "Conversar" (ck-chat 56, fantasma)
  article#hu-sound.ck-card (col 2): strong "Som do carro"; span 13px "Controles por Bluetooth/rádio"; div.ck-media-btns 3x 56x56 data-action media.previous / media.playpause / media.next ; button.hu-btn data-action="apps.open.music" "Abrir música"
  article#hu-car.ck-card (col 3): strong "Subaru"; p#diagnostic-status 13px muted (2 linhas) ; div.hu-chips 2x2 (56 alto): data-action="device.read.basic" "Diagnóstico" (ck-car) · data-action="catalog.open" data-module="bluetooth" "Telefone" (ck-phone) · data-action="apps.open.camera360" "Câmeras" (ck-camera) · button#connections "Internet" (ck-wifi)
nav#hu-tabs.hu-tabs: button#hu-tab-home.ck-tab.is-active "Início" (ck-home) · button#hu-tab-nav.ck-tab "Navegar" (ck-nav) · button.ck-tab data-action="apps.open.music" "Música" · button#hu-tab-harumi.ck-tab "Harumi" · button#open-apps.ck-tab "Apps"
```

- **1024x600:**
  - colunas de 322px;
  - linha 1 com 176px, linha 2 com 268px.
- **800x480 (`max-height:520px`):**
  - topo 32px, abas 72px, padding 10 14;
  - linha 1 com 140px, avatar 80x110, relógio 52px;
  - `.ck-card` com padding 10 14.
- **Largura até 600px:** uma coluna com rolagem e abas de 64px.

**Ligações (launcher.js reescrito):**
- `#home-road-map` e `#hu-tab-nav`: `harumiRoadMap.open(false)` e depois focar `#nav-dest` em 80ms.
- `#hu-cities`: abre o cockpit e clica em `#ck-cities-toggle` se `aria-expanded==="false"`.
- `#hu-tab-harumi`: `#talk.click()`.
- `#hu-tab-home`: `harumiShell.closeAll()`.
- `harumiLauncherUpdate` passa a renderizar em `#apps-installed-grid`, na tela Apps.
- Remover as referências a `#favorite-grid`, `#installed-grid`, `#show-*` e `#dock-*`, sem erro de JS.

**`#NAV`, `#MUSIC` e `#CAMERA360`** passam a ficar em Ajustes, visíveis como valor da linha.

**`harumi-shell.js`:**
- **`closeAll()`:** fecha apps, road-map e atlas (`close(false)`) e clica em `#close-assistant`, `#close-connectivity` e `#close` quando estiverem visíveis.
- **Aba ativa:** "apps" se `#apps-panel` estiver visível, "harumi" se `#assistant` estiver visível, senão "home".

## Conversa (`#assistant`)

É uma folha lateral à direita, sem moldura:
- `position:fixed; top:0; right:0; bottom:var(--ck-tab-h); width:min(560px,100%); z-index:6`;
- `background:var(--ck-glass-strong); border-left:1px solid var(--ck-stroke-hi); box-shadow:0 0 0 100vmax rgba(27,27,33,.5)`;
- largura de 100% quando a tela tiver até 900px.

```
div.hu-head: div#assistant-avatar-slot (64x88) · h2 "Harumi" 20px + span#assistant-status 13px muted · div.hu-wave aria-hidden (5 <i> 4x18 acento) · button#close-assistant.hu-icon-btn (56, ck-close, aria-label "Fechar")
div#conversation role=log (flex 1, overflow auto; bolhas 17px raio 16; Harumi à esquerda em --ck-glass; .user-message à direita rgba(210,160,189,.18); strong 12px acento)
p#dictation-preview (pílula 15px --ck-warn-bg)
div.assistant-input: textarea#question (h56 raio 28 fundo rgba(27,27,33,.7) borda --ck-stroke-hi) · button#send-question (56x56 redondo acento)
div.assistant-actions: button#listen.ck-talk data-action="assistant.listen" "Falar" · #finish-listening (hidden) · data-action="assistant.cancel" "Parar" (fantasma) · #continue-answer (hidden) · data-action="voice.greet" "Apresentação"
p.privacy 11px "Conversa, voz e reconhecimento neste aparelho. Use o teclado com o carro parado."
```

**Onda de voz:**
- Anima só `transform:scaleY` nas barras de `#assistant[data-voice="listening"] .hu-wave i`. Com `data-voice="speaking"`, anima mais rápido.
- Com movimento reduzido, as barras ficam estáticas em 60%.

## Apps (`#apps-panel`)

Tela inteira (full-bleed).

```
div.hu-head: h2 "Apps" · div.hu-seg role=tablist: #apps-tab-installed "Instalados" · #apps-tab-own "Da Harumi" · #apps-oem-tab "Central" · #apps-tab-more "Mais apps" · #apps-refresh.hu-icon-btn (ck-refresh) · #apps-all.hu-btn "Todos do Android" · #apps-close.hu-icon-btn (ck-close)
div.apps-scroll > div#apps-installed-grid.hu-tiles (harumiLauncherUpdate: ícone real 56 arredondado + nome 15px; vazio → p "Abra o APK para ver os apps deste Android") + div#apps-grid.hu-tiles (catálogo)
```

- **Tile:** `button.app-card` de 148x120.
  - Círculo de 56px com ícone de linha: ck-nav para a navegação própria, ck-chat para a conversa, ck-globe para o atlas, ck-apps para OEM. Quando o app estiver instalado, o PNG real.
  - `h3` com 15px e `p.app-availability` com 12px, em uma linha.
  - Sem `app-detail` e sem "Origem da referência" na tela.
- **Colunas da grade:** 5 a partir de 900px, 4 em 800px e 2 no celular.
- **Segmentos:** own com 3, oem com 17, "Mais apps" com os 7 não instalados, rotulados "Ver na loja".
- **`#apps-install`:** vira um chip.
- **Manter:** `harumiAppsUpdate`, `harumiApps.{open,close,isOpen,refresh}` e as ações `catalog.*`.

## Ajustes (`#settings`)

Tela inteira (full-bleed), com cabeçalho `hu-head`: h2 "Ajustes" e `button#close.hu-icon-btn`.

Lista `div.hu-row-list`. Cada linha `div.hu-row` tem altura de 64px ou mais, com ícone, rótulo de 17px, valor de 13px em muted e um botão de 56px à direita.

**Linhas:**
- **Mapas:** valor `#NAV`; botão `data-action="apps.choose" data-module="NAV"` "Escolher".
- **Música:** valor `#MUSIC`; mesmo botão de escolher.
- **Câmeras 360°:** valor `#CAMERA360`; mesmo botão de escolher.
- **Comando "Oi Harumi":** botão `#wake-toggle`. O texto vem do app.js.
- **Pronúncia:** botão `#wake-learn` "Ensinar".
- **Internet:** botão que faz `#connections.click()`.
- **Interface de fábrica:** `data-action="oem.home"`, botão fantasma.

## Internet (`#connectivity`)

- **Cabeçalho `hu-head`:** h2 "Internet", `p#network-status` com 19px e `#close-connectivity`.
- **Configuração inicial:** dois cartões (Wi-Fi e Bluetooth, com ícone, uma frase e botão de 56px `connection.wifi` / `connection.bluetooth`) dentro de `details#initial-network-setup`, que é mantido porque o test_internet_034 o usa. O `summary` vira chip de 56px.
- **Texto de rodapé:** `p.privacy` com "A IA e a voz locais funcionam sem rede."

## Atlas (`#brazil-atlas`)

- **Cabeçalho `hu-head`:** "Seu próximo destino" + h2 "Brasil", `#open-road-map.ck-chip` "Traçar rota" (ID mantido), `#atlas-native-nav.hu-btn` "Outros apps" e `#atlas-close`.
- **Layout:** grid de 1.1fr e 1fr. O mapa fica sem moldura e `.atlas-detail.ck-card` à direita.
- **Seletor:** altura de 56px, raio 12.
- **Capital e foto:** capital com 31px e foto com raio 12.
- **Botão de rota:** `#atlas-route.ck-talk`.
- **Cores dos estados:**
  - normal: `.atlas-state{fill:#3d3443;stroke:#8f7489}`;
  - hover: `#5c4458`;
  - selecionado: `var(--ck-accent)`.

## Mensagem `#message`

`position:fixed; top:48px; left:50%; transform:translateX(-50%); max-width:640px; background:var(--ck-glass-strong); border:1px solid var(--ck-stroke-hi); z-index:12`.

## Não fazer

- Mapa ao vivo na Home.
- ETA na Home.
- Cartões sem dado real, como clima, agenda ou capa de música.
- Alterar road-map.css, road-map.js, map3d.js, avatar.js, app.js, Java, build.gradle.kts ou os arquivos offline.
- Usar a classe `.ck-tabs` na barra global: usar `.hu-tabs`.
- Renomear IDs.
- Esconder `#open-road-map` ou `#open-apps` do DOM.
- Usar `backdrop-filter`.
- Downloads.
- Commit.
- Apagar os CSS mortos ou os ícones coloridos nesta rodada.
