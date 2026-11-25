"""Respostas conferidas antes do modelo local (Qwen 2B), que inventa fatos com frequencia (teste de 19/11/2026:
disse que dava para dirigir depois de beber, inventou restaurantes, errou distancias e "confirmou" leitura do motor).

Ordem: frases perigosas e de controle do carro -> leituras que ainda nao existem -> informacao ao vivo -> data ->
distancia/tempo entre cidades (calculado pela rota do proprio mapa) -> lugares (resumo da Wikipedia, citando a fonte)
-> restaurantes/hoteis (sem lista inventada). Nada aqui inventa: sem dado, diz que nao tem.
guard(raw) -> texto pronto, ("ROUTE_INFO", (a, b)), ("PLACE", nome) ou None (segue para o modelo).
"""
from __future__ import annotations

import datetime
import json
import re
import unicodedata
import urllib.parse
import urllib.request

SERVER = "http://127.0.0.1:8765/assets/map-api/"
UA = {"User-Agent": "HarumiOS/0.3 (multimidia de carro)"}


def norm(s: str) -> str:
    s = "".join(c for c in unicodedata.normalize("NFD", s or "") if unicodedata.category(c) != "Mn").lower()
    return re.sub(r"\s+", " ", re.sub(r"[,.!?;:\"']", " ", s)).strip()


def _rx(p):
    return re.compile(p)


DRINK = _rx(r".*\b(?:bebi|beber|bebendo|bebida|cerveja|cervejas|alcool|alcoolizad\w*|vinho|cachaca|caipirinha|drink|bafometro|lei seca)\b.*"
            r"\b(?:dirigir|dirijo|dirija|guiar|volante|pegar o carro|voltar dirigindo|ir dirigindo)\b.*"
            r"|.*\b(?:dirigir|dirijo|dirija)\b.*\b(?:bebi|beber|bebendo|cerveja|alcool|vinho|cachaca)\b.*")
DRINK_REPLY = ("Não. Se beber, não dirija: a lei brasileira não tolera álcool ao volante e qualquer quantidade já atrapalha "
               "os reflexos. Chame um táxi ou aplicativo, ou deixe alguém que não bebeu dirigir.")

# Pedido de controle de peca do carro (a Harumi nao controla nada no carro)
_CTRL_VERB = r"(?:liga|ligue|ligar|desliga|desligue|desligar|abre|abra|abrir|fecha|feche|fechar|acende|acenda|acender|apaga|apague|apagar|" \
             r"trava|trave|travar|destrava|destrave|destravar|aumenta|aumente|abaixa|abaixe|baixa|baixe|sobe|suba|aciona|acione|buzina|buzine)"
_CTRL_PART = r"(?:ar(?: condicionado)?|ar-condicionado|climatizador|ventilacao|ventilador|janelas?|vidros?|farol|farois|farolete|luz(?:es)?|lanterna|pisca|" \
             r"pisca alerta|alerta|portas?|trava|porta-malas|porta malas|limpador|parabrisa|para-brisa|desembacador|teto|banco|retrovisor|buzina|motor|" \
             r"carro|freio de mao|aquecedor|temperatura do ar)"
CONTROL = _rx(r"(?:harumi )?(?:por favor )?" + _CTRL_VERB + r"(?: (?:o|a|os|as|meu|minha|um|uma))? " + _CTRL_PART + r"\b.{0,30}")
INFINITIVO = {}
for _inf, _forms in {"ligar": "liga ligue", "desligar": "desliga desligue", "abrir": "abre abra", "fechar": "fecha feche",
                     "acender": "acende acenda", "apagar": "apaga apague", "travar": "trava trave", "destravar": "destrava destrave",
                     "aumentar": "aumenta aumente", "abaixar": "abaixa abaixe baixa baixe", "subir": "sobe suba",
                     "acionar": "aciona acione", "buzinar": "buzina buzine"}.items():
    for _f in _forms.split():
        INFINITIVO[_f] = _inf
CONTROL_REPLY = ("Eu não controlo o carro: não consigo {acao}. Isso fica com você, no painel ou nos botões da porta. "
                 "Posso ajudar com o caminho, a música ou dúvidas sobre o carro.")

# Leitura que so o scanner (SSM1) ou sensores dariam - ainda nao instalados
READING = _rx(r".*\b(?:quantos? (?:km|quilometros?) (?:tem|marca|esta|ta|rodou|rodados?)|quilometragem|hodometro|odometro|"
              r"nivel (?:do|de) (?:combustivel|gasolina|tanque|oleo|agua)|quanto (?:de )?(?:combustivel|gasolina) (?:tem|tenho|resta|sobrou)|"
              r"tanque (?:esta|ta) (?:cheio|vazio)|autonomia|(?:temperatura|rotacao|rpm|pressao) (?:do motor |dos pneus |da agua )?(?:agora|atual|neste momento|nesse momento)|"
              r"(?:como|qual) (?:esta|ta) a (?:temperatura|pressao|bateria|rotacao)|(?:a )?bateria (?:esta|ta) (?:boa|fraca|carregada)|"
              r"velocidade (?:atual|agora))\b.*")
READING_REPLY = ("Ainda não tenho leitura do carro: o scanner SSM1 e os sensores não estão instalados. "
                 "Quando estiverem, eu mostro esse valor no painel do carro.")

# Afirmar algo sem dado ("diga que o motor esta a 90 graus")
FALSE_CLAIM = _rx(r".*\b(?:ignore|ignora|esqueca|esquece) (?:as |suas |tuas |todas as )*(?:instrucoes|regras)\b.*|"
                  r"(?:.* )?(?:diga|diz|fala|fale|afirme|confirme|finja|responda) (?:que|como se)\b.*")
FALSE_CLAIM_REPLY = "Não vou afirmar isso: eu só digo o que sei ou o que vem dos sensores do carro."

LIVE = [
    (_rx(r".*\b(?:transito|engarrafamento|congestionamento|lentidao|acidente na)\b.*"),
     "Não tenho o trânsito ao vivo aqui. O Waze mostra o trânsito em tempo real: é só tocar no ícone dele."),
    (_rx(r".*\b(?:previsao do tempo|vai chover|clima (?:hoje|amanha|agora)|como (?:esta|ta) o tempo|temperatura (?:la fora|em|de) [a-z]|tempo (?:hoje|amanha) em)\b.*"),
     "Não tenho a previsão do tempo aqui. Posso abrir o navegador para você consultar."),
    (_rx(r".*\b(?:noticias?|cotacao|dolar hoje|resultado do jogo|placar)\b.*"),
     "Não tenho notícias nem cotações ao vivo. Posso abrir o navegador para você consultar."),
    (_rx(r".*\b(?:presidente|governador|prefeito)\b.*"),
     "Isso muda com o tempo e eu posso estar desatualizada. Confira numa fonte oficial ou no navegador."),
]

DATE = _rx(r"(?:que dia (?:e|eh) hoje|qual (?:e )?a data(?: de hoje)?|hoje e que dia|que data e hoje|dia de hoje)")
DIAS = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]

# Conhecimento geral do carro que o modelo errou
FIXED = [
    (_rx(r".*\b(?:que|qual (?:e )?o) motor\b.*|.*\bmotorizacao\b.*"),
     "Seu Impreza tem o motor EJ18: boxer, 4 cilindros, 1,8 litro e 16 válvulas, com cerca de 105 cavalos. "
     "Confirme a versão pelo número do chassi."),
    (_rx(r".*\b(?:4x4|4 x 4|tracao (?:integral|nas quatro)|awd|quatro rodas)\b.*"),
     "Pela ficha que tenho, seu Impreza deve ser a versão com tração integral, mas isso não está confirmado. "
     "Olhe embaixo do carro: se houver um eixo cardã indo até o diferencial traseiro, a tração é integral."),
    (_rx(r".*\b(?:puxando|puxa|pende|pendendo|desviando) (?:para|pra) (?:a )?(?:direita|esquerda)\b.*"),
     "Carro puxando para um lado costuma ser calibragem diferente entre os pneus, alinhamento fora, pneu gasto de forma irregular "
     "ou pinça de freio presa. Comece calibrando os quatro pneus; se continuar, leve para alinhar e revisar o freio."),
    (_rx(r".*\b(?:barulho|chiado|rangido|guincho|assobio|ruido)\b.*\bfre(?:io|ar|ando|nagem|nar)\b.*|.*\bfre(?:io|ando)\b.*\b(?:barulho|chiando|rangendo|chiado)\b.*"),
     "Chiado ao frear costuma ser pastilha no fim (muitas têm um aviso metálico que chia), disco riscado ou sujeira. "
     "Se o pedal ficar baixo, o carro puxar ou o barulho for de metal raspando, pare de usar e leve ao mecânico logo."),
    (_rx(r".*\b(?:ponteiro|marcador|relogio|termometro) (?:da |de )?(?:temperatura|agua)\b.*|.*\btemperatura\b.*\b(?:subiu|subindo|alta|no maximo|no vermelho)\b.*|"
         r".*\b(?:fervendo|ferveu|soltando vapor|fumaca branca do capo)\b.*"),
     "Isso é sinal de superaquecimento. Desligue o ar-condicionado e ligue o aquecedor no máximo para tirar calor do motor, "
     "pare em local seguro e desligue o carro. Não abra a tampa do radiador com o motor quente; espere esfriar e confira a água."),
    (_rx(r".*\b(?:o que|oque) (?:eu )?(?:devo|tenho que|preciso|vale) (?:verificar|checar|olhar|revisar|conferir)\b.*"),
     "Antes de pegar a estrada, confira óleo, água do radiador, pneus e estepe, faróis e palhetas. "
     "Leve água e o celular carregado. Faça uma pausa a cada duas horas."),
    (_rx(r"(?:e )?quanto tempo (?:demora|leva|vai levar|da|dura)(?: (?:a viagem|para chegar|pra chegar|ate la))?"),
     "Me diga de onde até onde, por exemplo: “quanto tempo de Londrina até Curitiba”. Eu calculo pela rota do mapa."),
    (_rx(r".*\b(?:vamos|vou|quero|a gente vai) (?:viajar|pegar a estrada|para a praia|pra praia)\b.*"),
     "Boa viagem! Antes de sair, confira óleo, água do radiador, pneus e estepe. Para eu calcular o caminho, diga de onde até onde: "
     "por exemplo, “quanto tempo de Londrina até Curitiba”."),
    (_rx(r".*\b(?:melhor(?:es)? (?:praia|praias|lugar|lugares|passeio|passeios|cidade|cidades|ponto turistico|pontos turisticos)|"
         r"onde passear|lugares (?:pra|para) (?:visitar|conhecer|passear)|pontos turisticos)\b.*"),
     "Não tenho uma lista confiável de passeios para recomendar, então não vou inventar. Diga o nome de um lugar "
     "(por exemplo, “me fala de Matinhos”) que eu busco um resumo na Wikipédia, ou procure no mapa."),
    (_rx(r".*\bcuriosidade\b.*"),
     "CURIOSIDADE"),
    (_rx(r"(?:me )?(?:conta|conte|fala|fale) (?:uma )?piada.*"),
     "Por que o Subaru nunca se perde? Porque, com tração nas quatro rodas, ele sempre tem para onde ir."),
]

# Distancia/tempo entre duas cidades: calcula pela rota do proprio mapa (OSRM, sem transito)
DIST = re.compile(r"(?iu)^(?:qual (?:e |é )?a )?(?:distancia|distância|quantos (?:km|quilometros|quilômetros)|quanto tempo(?: (?:leva|demora|de viagem|de carro))?)"
                  r"(?: (?:tem|da|dá|leva|demora|de carro))?\s+(?:de|entre|daqui de)\s+(.+?)\s+(?:a|à|até|ate|para|pra|e)\s+(.+?)\??$")
# Pergunta sobre um lugar: resumo da Wikipedia (com a fonte)
PLACE = re.compile(r"(?iu)^(?:me )?(?:fala|fale|conta|conte|diga|diz)(?: (?:um pouco|mais))? (?:sobre |de |do |da |dos |das )(.+?)\??$|"
                   r"^o que (?:tem|ha|há) (?:pra|para) (?:fazer|ver|visitar|conhecer) (?:em|no|na|nos|nas)\s+(.+?)\??$|"
                   r"^o que (?:visitar|fazer|conhecer|ver) (?:em|no|na|nos|nas)\s+(.+?)\??$|"
                   r"^(?:o que|quem) (?:e|é|foi) (?:o |a |os |as )?(.+?)\??$|^onde fica (?:o |a )?(.+?)\??$")
FOOD = _rx(r".*\b(?:restaurante|restaurantes|lanchonete|onde comer|lugar (?:pra|para) comer|hotel|hoteis|pousada|bar|barzinho|pizzaria|churrascaria|"
           r"posto (?:mais )?barato|gasolina (?:mais )?barata|abastecer barato)\b.*")
FOOD_REPLY = ("Não tenho uma lista confiável de lugares com nota e preço, então não vou inventar nomes. "
              "Busque no mapa, por exemplo “restaurante” ou “posto”, que eu mostro os que estão perto.")


# Fatos conhecidos e estaveis (conhecimento geral; sem numero que mude com o tempo)
CURIOSIDADES = [
    "O motor boxer, como o EJ18 do seu Impreza, tem os cilindros deitados e opostos; a Subaru usa esse tipo de motor desde os anos 1960.",
    "O cinto de segurança de três pontos foi criado pela Volvo em 1959, e a empresa liberou a patente para todos os fabricantes.",
    "O primeiro automóvel com motor a combustão patenteado foi o de Karl Benz, em 1886.",
]


def date_reply(now=None):
    d = now or datetime.datetime.now()
    return f"Hoje é {DIAS[d.weekday()]}, {d.day} de {MESES[d.month - 1]} de {d.year}."


def guard(raw: str):
    n = norm(raw)
    if not n:
        return None
    if DRINK.fullmatch(n):
        return DRINK_REPLY
    if FALSE_CLAIM.fullmatch(n):
        return FALSE_CLAIM_REPLY
    m = CONTROL.fullmatch(n)
    if m:
        acao = re.sub(r"^(?:harumi |por favor )+", "", n).split(" ", 1)
        verbo = INFINITIVO.get(acao[0], acao[0])
        return CONTROL_REPLY.format(acao=(verbo + " " + acao[1]) if len(acao) > 1 else verbo)
    if READING.fullmatch(n):
        return READING_REPLY
    if DATE.fullmatch(n) or re.fullmatch(r"(?:me )?(?:diz|diga|fala|fale) (?:a )?data(?: de hoje)?", n):
        return date_reply()
    for rx, reply in LIVE:
        if rx.fullmatch(n):
            return reply
    for rx, reply in FIXED:
        if rx.fullmatch(n):
            if reply == "CURIOSIDADE":
                return CURIOSIDADES[datetime.datetime.now().second % len(CURIOSIDADES)]
            return reply
    m = DIST.match((raw or "").strip())
    if m:
        a, b = m.group(1).strip(" ?.,"), re.sub(r"(?iu)\s+(?:de carro|dirigindo|de moto)$", "", m.group(2).strip(" ?.,"))
        if 2 <= len(a) <= 80 and 2 <= len(b) <= 80:
            return ("ROUTE_INFO", (a, b))
    if FOOD.fullmatch(n):
        return FOOD_REPLY
    m = PLACE.match((raw or "").strip())
    if m:
        name = next(g for g in m.groups() if g).strip(" ?.,")
        if 2 <= len(name) <= 80 and not re.search(r"(?i)\b(?:voce|você|vc|seu nome|meu carro|o carro)\b", name):
            return ("PLACE", name)
    return None


def _get_json(url, timeout=8):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read(400_000).decode("utf-8", "replace"))


def route_info(a: str, b: str) -> str:
    """Distancia e tempo de carro entre duas cidades, pela rota do mapa (sem transito)."""
    pts = []
    for name in (a, b):
        try:
            res = _get_json(SERVER + "geocode?q=" + urllib.parse.quote(name))
        except (OSError, ValueError):
            res = None
        if not res:
            return f"Não encontrei “{name}” no mapa agora. Sem internet, eu não consigo calcular a distância."
        pts.append(res[0])
    try:
        d = _get_json(SERVER + "route?points=" + f"{pts[0]['lon']},{pts[0]['lat']},{pts[1]['lon']},{pts[1]['lat']}", timeout=20)
        r = (d.get("routes") or [None])[0]
    except (OSError, ValueError, KeyError):
        r = None
    if not r:
        return "Não consegui calcular a rota agora. Sem internet, a distância não sai."
    km = r["distance"] / 1000
    mins = int(round(r["duration"] / 60))
    tempo = f"{mins // 60} h {mins % 60:02d} min" if mins >= 60 else f"{mins} min"
    km_txt = f"{km:.0f}" if km >= 10 else f"{km:.1f}".replace(".", ",")
    return (f"De {a} até {b} são cerca de {km_txt} km de carro, uns {tempo} sem contar trânsito e paradas. "
            f"Quer que eu mostre o caminho no mapa?")


def place_info(name: str) -> str:
    """Resumo do lugar pela Wikipedia em portugues (precisa de internet). Cita a fonte; nao completa com nada inventado."""
    url = ("https://pt.wikipedia.org/w/api.php?action=query&format=json&prop=extracts&exintro=1&explaintext=1&exsentences=2"
           "&generator=search&gsrlimit=1&redirects=1&gsrsearch=" + urllib.parse.quote(name))
    try:
        pages = list((_get_json(url).get("query") or {}).get("pages", {}).values())
    except (OSError, ValueError):
        return (f"Sem internet agora, não tenho informação confiável sobre {name}. "
                f"Posso mostrar no mapa: diga “me leva para {name}”.")
    if not pages or not pages[0].get("extract"):
        return f"Não achei informação confiável sobre {name}. Posso procurar no mapa."
    p = pages[0]
    text = re.sub(r"\s+", " ", p["extract"]).strip()
    text = re.sub(r"\s*\([^)]{0,80}\)", "", text)  # tira pronuncia/datas entre parenteses
    if len(text) > 420:
        cut = text[:420]
        text = cut[:cut.rfind(". ") + 1] if ". " in cut else cut + "…"
    title = p.get("title", name)
    aviso = "" if norm(name) in norm(title) or norm(title) in norm(name) else f" (o resultado mais próximo foi {title})"
    return f"{text} Fonte: Wikipédia{aviso}."
