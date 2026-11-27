"""Assistente da Harumi no Linux: comandos locais (porta do LocalCommandParser.java) + IA local via llama-server.

O llama-server (llama.cpp) roda como servico separado em 127.0.0.1:8090 com o Qwen3.5 2B.
Comandos reconhecidos (rota, mapa, musica, parar...) nao passam pelo modelo.
"""
from __future__ import annotations

import json
import re
import threading
import unicodedata
import urllib.request
from datetime import datetime
from pathlib import Path

import harumi_guard

LLM_URL = "http://127.0.0.1:8090/v1/chat/completions"
KNOWLEDGE_FILE = Path(__file__).resolve().parent / "car_knowledge.json"

PERSONA = (
    "Você é Harumi, copiloto de Lucas no Subaru Impreza dele. Fale em português, de forma simpática e prática. "
    "Você ajuda com: dicas de direção e economia de combustível, segurança, manutenção e funcionamento do carro, "
    "estradas, rotas, viagens, cidades e pontos turísticos do Brasil, paradas e abastecimento, música e apps. "
    "Sempre responda a esses assuntos com dicas úteis. "
    "Use no máximo três frases curtas e termine sempre a última. "
    "Não invente números, nomes, datas, leituras do carro ou rotas. "
    "Sobre lugares, use só conhecimento geral e sugira conferir no mapa. "
    "Você não controla o ar-condicionado, os vidros, as luzes nem nenhuma peça do carro: nunca diga que ligou, "
    "ajustou ou fez algo no carro; no máximo sugira o que o motorista pode fazer. "
    "Não fale do diagnóstico se não perguntarem. Nunca use emojis. "
    "Você não tem trânsito, clima, combustível, quilometragem, temperatura nem nenhum estado atual do carro ou da rua: "
    "nunca diga como essas coisas estão. Não cite nomes de restaurantes, hotéis ou lojas. "
    "Se não tiver certeza de um fato, diga que não sabe em vez de chutar."
)
GREETING = "Oi, Lucas! Eu sou a Harumi! Quer que eu abra o mapa? Me diz: pra onde a gente vai hoje?"
OFF_TOPIC_REPLY = ("Esse assunto fica fora da minha área. Sou sua copiloto: posso ajudar com o carro, a estrada, "
                   "rotas, viagem, pontos turísticos e música.")
OFF_TOPIC = re.compile(r"(?s).*\b(?:medicina|doencas?|remedios?|medicamentos?|cancer|diabetes|depressao|ansiedade|gravidez|"
                       r"gravida|vacinas?|cirurgia|exame de sangue|consulta medica|advogad[oa]s?|juridic[oa]|jurisprudencia|"
                       r"processo judicial|peticao|sentenca|tribunal|inss|aposentadoria|politica|eleicao|eleicoes|deputad[oa]|"
                       r"senador[a]?|partido politico|investimentos?|bitcoin|criptomoedas?|bolsa de valores|imposto de renda|"
                       r"programacao|python|javascript|receita de|como cozinhar|culinaria|religiao|horoscopo|signo)\b.*")
BAD_PLACE = re.compile(r"(?is).*(?:[\x00-\x1f<>]|https?:|intent:|javascript:|file:|geo:).*")


# Conforto (so no Linux): conselho geral, sem dado especifico do carro. A Harumi nao controla o ar nem os vidros.
EXTRA = [
    {"id": "calor", "regex": r"\b(?:muito )?(?:calor|quente|abafado|sufocante)\b|\bderretendo\b",
     "answer": "Para refrescar: ligue o ar-condicionado no mais frio, com a ventilação forte e a recirculação ligada. "
               "Se o carro ficou no sol, abra os vidros no primeiro minuto para tirar o ar quente e depois feche."},
    {"id": "frio", "regex": r"\b(?:muito )?(?:frio|gelado|congelando)\b|\bvidro embacado\b|\bembaca\w*",
     "answer": "Com frio ou vidro embaçado, ligue a ventilação no para-brisa com o ar quente; o ar-condicionado ligado junto "
               "ajuda a tirar a umidade e desembaça mais rápido."},
]


def _load_knowledge():
    try:
        data = json.loads(KNOWLEDGE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = {"entries": [], "engine": [], "gearbox": []}
    entries = [(re.compile("(?s).*(?:" + e["regex"] + ").*"), e["answer"]) for e in data["entries"] + EXTRA]
    return entries, data.get("engine", []), data.get("gearbox", [])


KNOWLEDGE, ENGINE_CODES, GEAR_CODES = _load_knowledge()
CODE = re.compile(r"(?s).*\bcodigo (?:de (?:falha|erro|defeito) )?(?:numero )?(\d{2})\b.*")
GEARBOX = re.compile(r"(?s).*\b(?:cambio|transmissao|tcu|automatico)\b.*")


def car_answer(raw: str):
    """Resposta conferida (base do Android, docs/subaru) ou None para seguir ao modelo."""
    n = re.sub(r"\s+", " ", re.sub(r"[,.!?;:]", " ", norm(raw))).strip()
    m = CODE.match(n)
    if m:
        code, gear = m.group(1), bool(GEARBOX.match(n))
        if gear:
            return f"A caixa atual é manual AWD; não aplique códigos da TCU 4EAT. Confirme a origem do código {code} e a instalação elétrica com um profissional."
        for c in ENGINE_CODES:
            if c["code"] == code:
                place = "No câmbio automático" if gear else "No motor do seu Impreza"
                extra = " Essa informação tem uma fonte só; confirme com o mecânico." if c.get("singleSource") else ""
                return f"{place}, o código {code} indica {c['text']}.{extra}"
        return f"Não tenho o código {code} do {'câmbio' if gear else 'motor'} na minha base. Confira com o mecânico."
    for pattern, answer in KNOWLEDGE:
        if pattern.match(n):
            return answer
    return None


def quick_reply(raw: str):
    n = re.sub(r"\s+", " ", re.sub(r"[,.!?;:]", " ", re.sub(r"\b(?:harumi|rarumi)\b", " ", norm(raw)))).strip()
    greeting = r"(?:oi|ola|bom dia|boa tarde|boa noite)"
    wellbeing = r"(?:tudo bem|(?:esta|ta) tudo bem|como (?:vai(?: voce)?|voce (?:esta|ta|vai))|voce (?:esta|ta) bem)"
    unit = f"(?:{greeting}(?: {wellbeing})?|{wellbeing})"
    if re.fullmatch(f"{unit}(?: {unit}){{0,2}}", n):
        return "Oi, Lucas! Tudo bem por aqui. E você?"
    if re.fullmatch(r"(?:obrigad[oa]|valeu)(?: muito)?", n):
        return "Por nada, Lucas! Estou por aqui."
    return None


def norm(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s or "") if unicodedata.category(c) != "Mn").lower()


def about_car(raw: str) -> bool:
    return bool(re.match(r".*\b(?:carro|veiculo|motor|scanner|obd2?|ecu|bateria|oleo|temperatura do|luz de (?:injecao|alerta)|pane|falha no)\b.*", norm(raw)))


# ---- Comandos curtos e imperativos (volume, apps, hora, rota, tela limpa). So a frase inteira casa (fullmatch):
# pergunta como "o que e volume morto?" nao vira comando. A pagina/servidor executa; a Harumi so avisa o que vai fazer.
_ART = r"(?: (?:o|a|os|as|um|uma|meu|minha))?"
_SOFT = r" um pouco| bastante| mais"
_VOL_UP = re.compile(r"(?:aumenta|aumente|aumentar|sobe|suba|subir|eleva|eleve|mais)(?P<a>" + _SOFT + r")?" + _ART + r" (?:volume|som)(?P<b>" + _SOFT + r")?")
_VOL_DOWN = re.compile(r"(?:abaixa|abaixe|abaixar|diminui|diminua|diminuir|baixa|baixe|baixar|reduz|reduza|reduzir|menos)(?P<a>" + _SOFT + r")?" + _ART + r" (?:volume|som)(?P<b>" + _SOFT + r")?")
_VOL_SET = re.compile(r"(?:(?:poe|poem|coloca|bota|deixa|deixe|ajusta|ajuste|define|seta|regula) )?(?:o )?volume (?:em|para|pra|no|a|na) (\d{1,3})(?: ?%| por ?cento)?")
_VOL_MUTE = re.compile(r"(?:silencia|silencie|silenciar|muta|mute|mutar|cala|desliga o som|(?:poe|coloca|bota|ativa|ative) (?:o |no |em )?mudo|"
                       r"(?:poe|coloca|bota) o (?:volume|som) no mudo)(?: o)?(?: volume| som| audio)?")
_VOL_UNMUTE = re.compile(r"(?:tira|tire|tirar|desativa|desative|volta|volte|voltar)(?: o| do)? (?:mudo|volume|som)|"
                         r"(?:desmuta|desmute|desmutar)(?: o)?(?: volume| som| audio)?|tira do mudo")
_APPS = {"waze": ("waze", "Waze"), "claude": ("claude", "Claude"), "chatgpt": ("chatgpt", "ChatGPT"),
         "browser": ("browser", "navegador")}
_APP_NAMES = {
    "waze": r"waze|uaze|wase", "claude": r"claude|claud|clode|cloude",
    "chatgpt": r"chat ?gpt|chat g p t|chat gepete|chat jipiti|chat gipiti",
    "browser": r"navegador (?:de|da) (?:internet|web)|navegador web|browser|chrome|firefox|internet",
}
_OPEN_VERB = r"(?:abra|abrir|abre|abril|inicia|inicie|iniciar|liga|ligar|bota|coloca|poe)"
_CLOCK = re.compile(r"(?:que horas (?:sao|e)|que hora e|qual (?:e )?a hora|(?:me )?(?:diz|diga|fala|fale|informa|informe) (?:a hora|as horas|que horas sao)|hora certa)(?: agora| ai)?")
_ETA = re.compile(r"(?:quanto (?:tempo )?falta(?: (?:para|pra) chegar)?|quando (?:eu )?chego|quando (?:a gente |nos )?(?:vai |vamos )?chegar|"
                  r"que horas (?:eu )?chego|quanto falta (?:para|pra) (?:o )?destino)(?: la| ai)?")
_CLEAN_OFF = re.compile(r"(?:sai|saia|sair|desativa|desative|desativar|desliga|desligue|desligar|tira|tire|tirar|volta|volte|voltar|fecha|feche|fechar)"
                        r"(?: (?:do|da|de|o|a))?(?: modo)? tela limpa")
_CLEAN_ON = re.compile(r"(?:(?:ativa|ative|ativar|liga|ligue|ligar|entra|entre|entrar|coloca|poe|bota|abre|abra|abrir|muda|mude) (?:(?:o|no|em|para|pra) )?)?(?:modo )?tela limpa")
_CLOSE_APP = re.compile(r"(?:fecha|feche|fechar)(?: (?:o|a|esse|essa|este|esta|aquele|o meu))? (?:app|aplicativo|aplicacao|programa|janela)(?: atual| aberto| aberta)?")


def command(n: str):
    """n = frase normalizada (sem acento, minuscula, sem pontuacao final). Devolve (acao, dado) ou None."""
    n = re.sub(r"\s+", " ", re.sub(r" (?:pra|para) mim$", "", n)).strip()
    if len(n) > 60:
        return None
    for rx, sign in ((_VOL_UP, 1), (_VOL_DOWN, -1)):
        m = rx.fullmatch(n)
        if m:
            soft = "um pouco" in ((m.group("a") or "") + (m.group("b") or ""))
            return "VOLUME", ("step", sign * (5 if soft else 10))
    m = _VOL_SET.fullmatch(n)
    if m and int(m.group(1)) <= 100:
        return "VOLUME", ("set", int(m.group(1)))
    if _VOL_UNMUTE.fullmatch(n):
        return "VOLUME", ("mute", False)
    if _VOL_MUTE.fullmatch(n):
        return "VOLUME", ("mute", True)
    if _CLOCK.fullmatch(n):
        return "CLOCK", ""
    if _ETA.fullmatch(n):
        return "ETA", ""
    if _CLEAN_OFF.fullmatch(n):
        return "CLEAN", False
    if _CLEAN_ON.fullmatch(n):
        return "CLEAN", True
    if _CLOSE_APP.fullmatch(n):
        return "CLOSE_APP", ""
    for key, names in _APP_NAMES.items():
        if re.fullmatch(_OPEN_VERB + _ART + r"(?: app| aplicativo)?(?: (?:do|da|de))?" + _ART + r" (?:" + names + r")", n) or \
           re.fullmatch(_OPEN_VERB + r"(?: app| aplicativo)? (?:" + names + r")", n):
            return "OPEN_APP", key
    return None


def clock_reply(now=None) -> str:
    now = now or datetime.now()
    if now.minute == 0:
        return "É 1 hora em ponto." if now.hour == 1 else f"São {now.hour} horas em ponto."
    return f"Agora são {now.hour}h{now.minute:02d}."


def eta_reply(route) -> str:
    """route = {'distance': metros, 'duration': segundos (opcional)} da ultima rota calculada, ou None."""
    try:
        dist = float(route["distance"]) if route else 0.0
    except (KeyError, TypeError, ValueError):
        dist = 0.0
    if dist <= 0:
        return "Não há rota ativa no momento. Me diga para onde vamos e eu traço o caminho."
    txt = f"A última rota que tracei tem {dist / 1000:.1f} km".replace(".", ",") + " no total"
    try:
        sec = float(route.get("duration") or 0)
    except (TypeError, ValueError):
        sec = 0
    if sec > 0:
        mins = int(round(sec / 60))
        txt += f", cerca de {mins // 60}h{mins % 60:02d} de viagem sem trânsito" if mins >= 60 else f", cerca de {mins} min sem trânsito"
    return txt + ". Eu não acompanho o trecho já percorrido, então não sei quanto falta; confira no mapa."


def parse(raw: str):
    """Devolve (acao, dado). Acoes: GREETING, STOP, MAP, MUSIC, YOUTUBE, VOLUME, OPEN_APP, CLOSE_APP, CLOCK, ETA, CLEAN, ROUTE, ROUTE_BETWEEN, DIAGNOSTICS, OFF_TOPIC, CHAT."""
    if raw is None or len(raw) > 1600:
        raise ValueError("Pedido muito longo.")
    text = re.sub(r"(?iu)^(?:harumi|rarumi)[, ]+", "", raw.strip())
    text = re.sub(r"(?iu)[,.!?]+$", "", text)
    text = re.sub(r"(?iu)^(?:por favor[, ]+|(?:você |voce )?pode )", "", text)
    text = re.sub(r"(?iu)[, ]+por favor$", "", text)
    n = norm(text)
    if re.fullmatch(r"(?:oi|ola)(?:,? (?:harumi|rarumi))?", n):
        return "GREETING", ""
    if re.fullmatch(r"(pare|parar|cancele|cancelar|silencio)", n):
        return "STOP", ""
    if re.fullmatch(r"(?:abra|abrir|abre|abril)(?: o| os| um| uma)? (?:mapa|mapas|navegador|navegacao)(?: para (?:encontrar|ver|buscar|procurar).*)?", n):
        return "MAP", ""
    if re.fullmatch(r"(?:abra|abrir|abre|toque|toca|tocar|bota|coloca|liga|ligar)(?: a| o| uma| um)? (?:musica|spotify|som)", n):
        return "MUSIC", ""
    if re.fullmatch(r"(?:abra|abrir|abre|bota|coloca)(?: o| um)? (?:youtube|video|videos)", n):
        return "YOUTUBE", ""
    cmd = command(n)
    if cmd:
        return cmd
    if re.match(r".*(?:temperatura do motor|rotacao do motor|estado do carro|como esta o carro|problema no carro|status do motor|diagnostico).*", n):
        return "DIAGNOSTICS", ""
    m = re.match(r"(?iu)^(?:me )?(?:(?:trace|traça|traca|tracar|traçar|faça|faca) (?:uma |a )?rota(?: pra mim| para mim)?(?: no mapa)?|rota|navegue) de\s+(.+?)\s+(?:para|até|ate)\s+(.+)$", text)
    if m:
        a, b = m.group(1).strip(), m.group(2).strip()
        for p in (a, b):
            if len(p) < 2 or len(p) > 160 or BAD_PLACE.match(p):
                raise ValueError("Informe cidades sem links.")
        return "ROUTE_BETWEEN", (a, b)
    m = re.match(r"(?iu)^(?:(?:trace|traça|traca|traz|traçar|tracar) (?:uma |a )?rota para|fa[çc]a (?:uma |a )?rota para|navegue para|navegar para|"
                 r"me lev[ae] (?:para|pra|pro|até|ate|à|a|no|na|ao)|qual (?:é |e )?o caminho (?:até|ate|para|pro|pra)|onde fica|"
                 r"como vou (?:até|ate|para|pro|pra)|como fa[çc]o para chegar (?:em|no|na|ao)|(?:quero )?ir para|rota para|como chego (?:em|no|na))\s+(.+)$", text)
    if m:
        dest = m.group(1).strip()
        if len(dest) < 2 or len(dest) > 160 or BAD_PLACE.match(dest):
            raise ValueError("Informe um endereço ou nome de local, sem links.")
        dn = norm(dest)
        if not re.match(r"(?s).*(?:\?|[,;]\s*(?:e\s+)?(?:o que|qual|quais|como|onde|voce|vc|recomend|sugir)|\b(?:recomenda|sugere|indica)\b).*", dn) \
                and not (text.lower().startswith("onde fica") and about_car(dest)):
            return "ROUTE", dest
    if OFF_TOPIC.match(norm(raw)):
        return "OFF_TOPIC", ""
    known = quick_reply(raw) or car_answer(raw)
    if known:
        return "QUICK_REPLY", known
    g = harumi_guard.guard(raw)
    if isinstance(g, tuple):
        return g
    if g:
        return "QUICK_REPLY", g
    return "CHAT", ""


_EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿️‍]")


def tidy(text: str, max_sentences: int = 3) -> str:
    """Limpa a resposta do modelo: sem emoji, sem listas longas, no maximo 3 frases (a persona pede isso; o 2B nem sempre obedece)."""
    t = _EMOJI.sub("", text or "")
    t = re.sub(r"\s*\n+\s*", " ", t).strip()
    parts = re.split(r"(?<=[.!?])\s+", t)
    return " ".join(parts[:max_sentences]).strip()


class Assistant:
    """Liga o parser e o modelo a ponte de eventos (emit(fn, *args) chama window.fn na pagina)."""

    def __init__(self, emit, route_info=None):
        self.emit = emit
        self.route_info = route_info  # funcao sem argumentos -> {'distance': m, 'duration': s} da ultima rota, ou None
        self.lock = threading.Lock()
        self.session = 0
        self.busy = False
        self.history: list[dict] = []

    def status(self, text, busy):
        self.busy = busy
        self.emit("harumiUpdate", {"assistantStatus": text, "assistantBusy": busy,
                                   "animation": "thinking" if busy else "idle"})

    def cancel(self, feedback=False):
        with self.lock:
            self.session += 1
            was = self.busy
        if feedback and was:
            self.emit("harumiMessage", "Harumi", "Operação interrompida. Pode enviar uma nova mensagem.")
        self.status("Pronta · Orange Pi", False)

    def ask(self, question: str):
        try:
            action, data = parse(question)
        except ValueError as e:
            self.emit("harumiMessage", "Harumi", str(e))
            return
        if action == "STOP":
            self.cancel(True)
            return
        with self.lock:
            if self.busy:
                self.emit("harumiMessage", "Harumi", "Aguarde ou toque em Parar para interromper a operação atual.")
                return
            self.session += 1
            sid = self.session
            self.busy = True
        self.emit("harumiMessage", "Você", question)
        self.status("Pensando…", True)
        threading.Thread(target=self._run, args=(sid, question, action, data), daemon=True).start()

    def _valid(self, sid):
        return sid == self.session

    def _run(self, sid, question, action, data):
        reply, then = None, []
        try:
            if action == "GREETING":
                reply = GREETING
            elif action == "OFF_TOPIC":
                reply = OFF_TOPIC_REPLY
            elif action == "QUICK_REPLY":
                reply = data
            elif action == "MAP":
                reply, then = "Vou abrir o mapa.", [("harumiRoadMap.open", False)]
            elif action == "MUSIC":
                reply, then = "Vou abrir a música.", [("harumiLinuxOpen", "spotify")]
            elif action == "YOUTUBE":
                reply, then = "Vou abrir o YouTube.", [("harumiLinuxOpen", "youtube")]
            elif action == "OPEN_APP":
                reply, then = f"Vou abrir o {_APPS[data][1]}.", [("harumiLinuxOpen", _APPS[data][0])]
            elif action == "CLOSE_APP":
                reply, then = "Vou fechar o app.", [("harumiAssistCmd", {"type": "closeApp"})]
            elif action == "CLEAN":
                reply = "Vou ativar a tela limpa. Toque na tela para voltar." if data else "Vou sair da tela limpa."
                then = [("harumiAssistCmd", {"type": "cleanScreen", "on": bool(data)})]
            elif action == "CLOCK":
                reply = clock_reply()
            elif action == "ETA":
                try:
                    route = self.route_info() if self.route_info else None
                except Exception:
                    route = None
                reply = eta_reply(route)
            elif action == "VOLUME":
                reply, then = self._volume(*data)
            elif action == "ROUTE":
                reply, then = f"Vou traçar o caminho até {data}.", [("harumiRoadMap.navigateTo", data)]
            elif action == "ROUTE_BETWEEN":
                reply = "Vou mostrar o trajeto no mapa. O cálculo não considera trânsito em tempo real."
                then = [("harumiRoadMap.plan", data[0], data[1])]
            elif action == "ROUTE_INFO":
                reply = harumi_guard.route_info(*data)
            elif action == "PLACE":
                reply = harumi_guard.place_info(data)
            elif action == "DIAGNOSTICS":
                reply = "O diagnóstico do carro ainda não está conectado no Orange Pi."
            else:
                reply = self._chat(sid, question)
        except Exception:  # modelo fora do ar etc.
            reply = "A IA local ainda está carregando ou indisponível. Tente de novo em alguns segundos."
        if not self._valid(sid):
            return
        self.emit("harumiMessage", "Harumi", reply or "Não consegui montar uma resposta agora. Pode repetir?")
        for call in then:
            self.emit(call[0], *call[1:])
        with self.lock:
            if self._valid(sid):
                self.busy = False
        self.status("Pronta · Orange Pi", False)

    @staticmethod
    def _volume(kind, value):
        """Ajusta o volume do sistema (wpctl via harumi_system). Responde com o valor lido de volta, nunca presumido."""
        try:
            import harumi_system
            if kind == "step":
                v = harumi_system.step_volume(value)
            elif kind == "set":
                v = harumi_system.set_volume(value)
            else:
                cur = harumi_system.volume()
                v = harumi_system.toggle_mute() if cur is not None and bool(cur.get("muted")) != bool(value) else cur
        except Exception:
            v = None
        if not v:
            return "Não consegui ajustar o volume agora.", []
        text = "O som está no mudo." if v.get("muted") else f"Volume em {v.get('percent')}%."
        return text, [("harumiVolume", v)]

    def _chat(self, sid, question):
        msgs = [{"role": "system", "content": PERSONA}] + self.history[-6:] + [{"role": "user", "content": question}]
        body = json.dumps({"messages": msgs, "max_tokens": 200, "temperature": 0.25, "stream": True,
                           "chat_template_kwargs": {"enable_thinking": False}}).encode()
        req = urllib.request.Request(LLM_URL, data=body, headers={"Content-Type": "application/json"})
        text = ""
        with urllib.request.urlopen(req, timeout=120) as r:
            for line in r:
                if not self._valid(sid):
                    break
                line = line.strip()
                if not line.startswith(b"data:") or line == b"data: [DONE]":
                    continue
                try:
                    delta = json.loads(line[5:])["choices"][0]["delta"].get("content") or ""
                except (ValueError, KeyError, IndexError):
                    continue
                if delta:
                    text += delta
                    self.emit("harumiPartial", text.strip())
        # Pergunta factual curta: so a 1a frase (o 2B acerta o comeco e inventa complementos, ex.: "Curitiba... parque do Ibirapuera")
        factual = len(question) < 70 and re.match(r"(?:qual|quais|quem|quando|quanto|quantos|quantas|onde|em que ano)\b", norm(question).strip())
        text = tidy(text, 1 if factual else 3)
        if text and self._valid(sid):
            self.emit("harumiPartial", text)
        if text:
            self.history += [{"role": "user", "content": question}, {"role": "assistant", "content": text}]
            self.history = self.history[-12:]
        return text

