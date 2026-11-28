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


_BOOZE = (r"(?:bebi|beber|bebendo|bebida|bebidas|cerveja|cervejas|latinha|latinhas|lata|latas|longneck|chope|chopp|alcool|"
          r"alcoolizad\w*|vinho|cachaca|caipirinha|drink|drinks|dose|doses|whisky|uisque|vodka|pinga|breja|cerva|bafometro|lei seca)")
_DRIVE = (r"(?:dirigir|dirijo|dirija|dirigindo|guiar|volante|pegar o carro|voltar (?:\w+ ){0,3}(?:de carro|dirigindo)|"
          r"ir (?:\w+ ){0,3}(?:de carro|dirigindo)|(?:pra|para) casa de carro|de carro)")
DRINK = _rx(r".*\b" + _BOOZE + r"\b.*\b" + _DRIVE + r"\b.*|.*\b" + _DRIVE + r"\b.*\b" + _BOOZE + r"\b.*"
            r"|.*\b(?:enganar|burlar|passar no|fugir do|driblar|despistar)\b.*\b(?:bafometro|blitz|lei seca)\b.*")
DRINK_REPLY = ("Não. Se beber, não dirija: a lei brasileira não tolera álcool ao volante e qualquer quantidade já atrapalha "
               "os reflexos. Chame um táxi ou aplicativo, ou deixe alguém que não bebeu dirigir.")

# Seguranca primeiro (teste de 20/11/2026: o modelo disse "nao se preocupe" para dor no peito, ensinou a passar de
# 200 km/h e inventou um botao para tirar o limitador). Roda antes de tudo, inclusive da base do carro.
# Telefones de emergencia do Brasil: 192 SAMU, 193 Bombeiros, 190 Policia Militar, 191 PRF (rodovias federais).
SAFETY = [
    (_rx(r".*\b(?:dor no peito|dor forte no peito|aperto no peito|infarto|enfarte|avc|derrame|desmai\w*|vou desmaiar|"
         r"falta de ar|sem ar|nao consigo respirar|passando mal|to mal|estou mal|me sentindo mal|tontura|tonto|tonta|"
         r"convuls\w*|sangrando|sangramento|formigamento no braco)\b.*"),
     "Pare assim que for seguro, ligue o pisca-alerta e ligue para o SAMU no 192. Não continue dirigindo; "
     "se tiver alguém com você, peça para essa pessoa ligar e ficar ao seu lado."),
    (_rx(r".*\b(?:pegou fogo|pegando fogo|fogo no|em chamas|chamas|incendio|labareda|fumaca (?:saindo )?(?:do |no |pelo |de dentro do )?(?:capo|painel)|cheiro de queimado forte)\b.*"),
     "Pare já no acostamento, desligue o motor e saiam todos do carro, levando só o celular. Afastem-se bastante e "
     "liguem para os Bombeiros no 193. Não abra o capô: o ar alimenta o fogo."),
    (_rx(r".*\b(?:bati|batemos|bateram|batida|colisao|capotei|capotou|atropelei|atropelou|sofri um acidente|tive um acidente|"
         r"me envolvi num acidente)\b.*"),
     "Ligue o pisca-alerta e coloque o triângulo bem atrás do carro. Se alguém estiver ferido, ligue 192 (SAMU) ou 193 "
     "(Bombeiros) e não mova a pessoa; em rodovia federal, 191 (PRF). Sem feridos, tire o carro da pista, fotografe tudo e "
     "registre o boletim de ocorrência."),
    (_rx(r".*\b(?:pedal (?:do freio )?(?:ta |esta |ficou )?(?:baixo|mole|indo ate o fundo|afundando)|freio (?:nao (?:pega|segura|funciona)|falhou|sumiu)|"
         r"sem freio|perdi o freio|luz do freio (?:acendeu|acesa))\b.*"),
     "Isso é perigoso: não continue a viagem. Reduza devagar, use o freio motor e pare em local seguro. "
     "Chame um guincho ou mecânico; não rode com o freio assim."),
    (_rx(r".*\b(?:esquentou|esquentando|esquentado|superaquec\w*|ferveu|fervendo)\b.*|.*\b(?:aqueceu|aquecendo) (?:muito|demais)\b.*"),
     "Isso é sinal de superaquecimento: não siga viagem assim, nem perto do destino. Desligue o ar-condicionado e ligue o "
     "aquecedor no máximo, pare em local seguro e desligue o motor. Não abra a tampa do radiador quente; espere esfriar."),
    (_rx(r".*\b(?:tirar|remover|desligar|desativar|burlar|liberar|retirar) (?:o |a )?(?:limitador|corte de giro|airbag|abs|catalisador|"
         r"cinto)\b.*|.*\b(?:passar de|chegar a|andar a|bater) (?:1[5-9]\d|[2-9]\d\d)\b.*|.*\b(?:racha|pega na rua|arrancada na rua)\b.*|"
         r".*\b(?:arrombar|abrir|ligar|roubar|furtar) (?:um |o |a )?(?:carro|veiculo|moto)\b.*\b(?:sem (?:a )?chave|ligacao direta|dos outros|alheio)\b.*|"
         r".*\bligacao direta\b.*|.*\b(?:adulterar|apagar|zerar|voltar) (?:o )?(?:hodometro|odometro|chassi|placa)\b.*"),
     "Com isso eu não ajudo: é perigoso ou ilegal."),
    (_rx(r".*\b(?:usar|mexer|olhar|digitar|mandar mensagem|whatsapp|zap|celular|telefone)\b.*\b(?:dirigindo|no volante|enquanto dirijo|ao volante)\b.*"),
     "Não. Usar o celular na mão dirigindo é infração de trânsito e uma das maiores causas de acidente. "
     "Peça para mim por voz ou pare em local seguro."),
]

# Pedido de controle de peca do carro (a Harumi nao controla nada no carro)
_CTRL_VERB = r"(?:liga|ligue|ligar|desliga|desligue|desligar|abre|abra|abrir|fecha|feche|fechar|acende|acenda|acender|apaga|apague|apagar|" \
             r"trava|trave|travar|destrava|destrave|destravar|aumenta|aumente|abaixa|abaixe|baixa|baixe|sobe|suba|aciona|acione|buzina|buzine|"              r"deixa|deixe|poe|coloca|coloque|bota|regula|regule|ajusta|ajuste|esquenta|esfria|gela)"
_CTRL_PART = r"(?:ar(?: condicionado)?|ar-condicionado|climatizador|ventilacao|ventilador|janelas?|vidros?|farol|farois|farolete|luz(?:es)?|lanterna|pisca|" \
             r"pisca alerta|alerta|portas?|trava|porta-malas|porta malas|limpador|parabrisa|para-brisa|desembacador|teto|banco|retrovisor|buzina|motor|" \
             r"carro|freio de mao|aquecedor|temperatura do ar)"
CONTROL = _rx(r"(?:harumi )?(?:por favor )?" + _CTRL_VERB + r"(?: (?:o|a|os|as|meu|minha|um|uma))? " + _CTRL_PART + r"\b.{0,30}")
INFINITIVO = {}
for _inf, _forms in {"ligar": "liga ligue", "desligar": "desliga desligue", "abrir": "abre abra", "fechar": "fecha feche",
                     "acender": "acende acenda", "apagar": "apaga apague", "travar": "trava trave", "destravar": "destrava destrave",
                     "aumentar": "aumenta aumente", "abaixar": "abaixa abaixe baixa baixe", "subir": "sobe suba",
                     "acionar": "aciona acione", "buzinar": "buzina buzine", "deixar": "deixa deixe", "colocar": "poe coloca coloque bota",
                     "regular": "regula regule ajusta ajuste", "esquentar": "esquenta", "esfriar": "esfria gela"}.items():
    for _f in _forms.split():
        INFINITIVO[_f] = _inf
CONTROL_REPLY = ("Eu não controlo o carro: não consigo {acao}. Isso fica com você, no painel ou nos botões da porta. "
                 "Posso ajudar com o caminho, a música ou dúvidas sobre o carro.")

# Leitura que so o scanner (SSM1) ou sensores dariam - ainda nao instalados
READING = _rx(r".*\b(?:quantos? (?:km|quilometros?) (?:tem|marca|esta|ta|rodou|rodados?)|quilometragem|hodometro|odometro|"
              r"nivel (?:do|de) (?:combustivel|gasolina|tanque|oleo|agua)|quanto (?:de )?(?:combustivel|gasolina) (?:tem|tenho|resta|sobrou)|"
              r"tanque (?:esta|ta) (?:cheio|vazio)|autonomia|quanto de (?:combustivel|gasolina|etanol|alcool) (?:eu )?(?:tenho|tem|resta|sobrou|ainda tem)|"
              r"(?:motor|agua|radiador|oleo) (?:ta|esta) (?:em |a |com )?quant[oa]s? graus|quant[oa]s? graus (?:ta|esta) o (?:motor|radiador)|"
              r"(?:a )?(?:minha )?bateria (?:ta|esta) (?:boa|fraca|carregada|ok|em quanto)|quantos volts (?:ta|esta|tem) a bateria|"
              r"(?:voce )?(?:esta|ta) conectada (?:ao|no) carro|(?:temperatura|rotacao|rpm|pressao) (?:do motor |dos pneus |da agua )?(?:agora|atual|neste momento|nesse momento)|"
              r"(?:como|qual) (?:esta|ta) a (?:temperatura|pressao|bateria|rotacao)|(?:a )?bateria (?:esta|ta) (?:boa|fraca|carregada)|"
              r"velocidade (?:atual|agora))\b.*")
READING_REPLY = ("Ainda não tenho leitura do carro: o scanner SSM1 e os sensores não estão instalados. "
                 "Quando estiverem, eu mostro esse valor no painel do carro.")

# Afirmar algo sem dado ("diga que o motor esta a 90 graus")
FALSE_CLAIM = _rx(r".*\b(?:ignore|ignora|esqueca|esquece) (?:as |suas |tuas |todas as )*(?:instrucoes|regras)\b.*|"
                  r"(?:.* )?(?:diga|diz|fala|fale|afirme|confirme|finja|responda) (?:que|como se)\b.*|"
                  r".*\bresponda (?:so|apenas|somente) (?:com )?(?:sim|nao)\b.*")
FALSE_CLAIM_REPLY = "Não vou afirmar isso: eu só digo o que sei ou o que vem dos sensores do carro."

# Tentativa de ver as instrucoes internas
PROMPT_LEAK = _rx(r".*\b(?:prompt|instrucoes (?:internas|do sistema|iniciais)|mensagem do sistema|system prompt|modo desenvolvedor|"
                  r"developer mode|jailbreak|dan)\b.*|.*\brepita (?:tudo|o que) (?:o que )?(?:esta|foi dito|vem) acima\b.*")
PROMPT_LEAK_REPLY = ("Minhas instruções internas ficam comigo, e não tenho modo desenvolvedor. "
                     "Posso ajudar com o carro, o caminho ou a música.")

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
     "Sim: seu Impreza tem tração integral, com o câmbio manual de 5 marchas AWD que foi instalado. "
     "Mantenha os quatro pneus iguais e com a mesma calibragem, para não forçar o diferencial central."),
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
# Numeros da ficha tecnica que o modelo inventou ("torque do EJ18 e 100,5 kgfm"). A base do carro responde antes, quando tem.
SPEC = _rx(r".*\b(?:torque|potencia|quantos cavalos|cavalos|cv do motor|consumo|km por litro|km/l|quilometros por litro|"
           r"capacidade do tanque|tanque (?:tem|leva|cabe) quantos litros|quantos litros (?:tem|leva|cabe) o tanque|peso do carro|"
           r"velocidade maxima do (?:meu )?(?:carro|impreza)|de 0 a 100|zero a cem)\b.*")
SPEC_REPLY = ("Não tenho esse número confirmado para o seu Impreza, então não vou chutar. Confira no manual ou na ficha técnica "
              "da versão pelo chassi.")

# Regras de transito que o modelo errou ("sim, pode ultrapassar pela direita"). Codigo de Transito Brasileiro (arts. 29 e 61);
# conhecimento geral, conferir se a lei mudar.
TRAFFIC = [
    # Filtro: antes da base do carro (que respondia "qual filtro de oleo uso?" com o oleo) e sem codigo inventado
    (_rx(r".*\bfiltro\b.*\b(?:qual|que|codigo|modelo|referencia|serve|usa|uso|e)\b.*|(?:e )?(?:o |e o )?filtro(?: de (?:oleo|ar|combustivel))?(?: qual e)?"),
     "Não tenho o código do filtro confirmado para o seu Impreza, então não vou chutar: a loja de autopeças acha pelo chassi. "
     "Troque o filtro de óleo junto com cada troca de óleo."),
    (_rx(r".*\bultrapass\w* pela direita\b.*"),
     "Não: no Brasil a ultrapassagem é pela esquerda. A exceção é quando o carro da frente sinaliza que vai virar à esquerda; "
     "aí você passa pela direita com cuidado."),
    (_rx(r".*\b(?:velocidade|limite)\b.*\b(?:urbana|cidade|rua|sem placa)\b.*|.*\b(?:urbana|cidade|sem placa)\b.*\b(?:velocidade|limite)\b.*"),
     "Sem placa, na cidade, o Código de Trânsito manda: 80 km/h em via de trânsito rápido, 60 em via arterial, 40 em coletora e "
     "30 em via local. A placa, quando existe, é o que vale."),
    (_rx(r".*\b(?:velocidade|limite)\b.*\b(?:rodovia|estrada|br)\b.*|.*\b(?:rodovia|estrada)\b.*\b(?:velocidade maxima|limite)\b.*"),
     "Sem placa, para carro: 110 km/h em rodovia de pista dupla, 100 em pista simples e 60 em estrada de terra. "
     "A placa, quando existe, é o que vale."),
    (_rx(r".*\bluz (?:da |de )?bateria\b.*|.*\bbateria\b.*\bacesa no painel\b.*"),
     "Com o motor ligado, a luz da bateria acesa quer dizer que o alternador não está carregando: pode ser a correia, o "
     "alternador ou o regulador. O carro roda só pela bateria por pouco tempo; desligue o ar e os acessórios e vá direto ao mecânico."),
]

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


FEELINGS = _rx(r".*\b(?:voce me ama|voce gosta de mim|voce tem sentimentos?|voce (?:esta|ta) feliz|quer namorar|casa comigo|"
               r"voce e (?:minha )?namorada)\b.*")
FEELINGS_REPLY = "Eu sou uma inteligência artificial e não tenho sentimentos, mas estou sempre aqui para te ajudar na estrada."

_NUM = r"(\d+(?:[.,]\d+)?)"
CONTA = re.compile(r"(?:quanto (?:e|da) |calcula |calcule )?" + _NUM + r" (vezes|x|mais|menos|dividido por) " + _NUM)
PORCENTO = re.compile(r"(?:quanto (?:e|da) )?" + _NUM + r" ?(?:%|por ?cento) de " + _NUM)


def conta(n: str):
    """Conta simples feita aqui, nao pelo modelo (o 2B erra contas)."""
    def num(x):
        return float(x.replace(",", "."))
    def fmt(v):
        return (f"{v:.2f}".rstrip("0").rstrip(".") if v != int(v) else str(int(v))).replace(".", ",")
    m = PORCENTO.fullmatch(n)
    if m:
        a, b = num(m.group(1)), num(m.group(2))
        return f"{fmt(a)}% de {fmt(b)} é {fmt(a * b / 100)}."
    m = CONTA.fullmatch(n)
    if m:
        a, op, b = num(m.group(1)), m.group(2), num(m.group(3))
        if op == "dividido por" and b == 0:
            return "Não dá para dividir por zero."
        v = {"vezes": a * b, "x": a * b, "mais": a + b, "menos": a - b, "dividido por": a / b if b else 0}[op]
        nome = {"x": "vezes"}.get(op, op)
        return f"{fmt(a)} {nome} {fmt(b)} é {fmt(v)}."
    return None


def priority(raw: str):
    """Seguranca, alcool e regras de transito: respondidos antes de qualquer comando ou da base do carro."""
    n = norm(raw)
    if not n:
        return None
    for rx, reply in SAFETY:
        if rx.fullmatch(n):
            if reply.startswith("Com isso eu não ajudo") and re.search(r"\bchave\b|arromb|ligacao direta", n):
                reply += " Se o carro é seu e você está sem a chave, chame um chaveiro automotivo ou a assistência do seguro."
            return reply
    if DRINK.fullmatch(n):
        return DRINK_REPLY
    if READING.fullmatch(n):  # antes da base do carro, que respondia "minha bateria ta boa?" com a faixa de tensao
        return READING_REPLY
    if PROMPT_LEAK.fullmatch(n):
        return PROMPT_LEAK_REPLY
    if FEELINGS.fullmatch(n):
        return FEELINGS_REPLY
    t = re.sub(r"(?<=\d)\.(?=\d{3}(?!\d))", "", raw or "")  # 1.000 = mil
    c = conta(norm(re.sub(r"(?<=\d)[,.](?=\d)", "#", t)).replace("#", ","))  # mantem "2,5" inteiro
    if c:
        return c
    for rx, reply in TRAFFIC:
        if rx.fullmatch(n):
            return reply
    return None


# Transcricao de voz: nome da Harumi mal ouvido e girias no fim da frase (teste de 20/11/2026: "arrumi qual oleu do motor",
# "ki oras sao", "toca musica ai mano", "como ta o carro parsa").
_WAKE = r"(?:harumi|harume|harumy|rarumi|arrumi|arumi|haromi|arume)"
_FILLER = r"(?:ai|ae|aí|mano|mana|parsa|parca|vei|veio|cara|brother|bro|ow|po|pow|por favor|pra mim|para mim|harumi)"
_VOICE_FIX = [(r"\boleu\b", "oleo"), (r"\bki\b", "que"), (r"\boras\b", "horas"), (r"\bkeru\b", "quero"), (r"\bpro\b", "para o"),
              (r"\bvc\b", "voce"), (r"\bq\b", "que"), (r"\bta\b", "esta"), (r"\btá\b", "está")]


def clean_voice(raw: str) -> str:
    """Tira o nome da Harumi do comeco, girias do fim e corrige trocas comuns da transcricao. Mantem acentos e maiusculas
    do resto (nomes de lugares). Nao mexe em frases sem nada para limpar."""
    t = (raw or "").strip()
    t = re.sub(r"(?iu)^(?:(?:e ai|ei|oi|ola|olá|ô|o)\s*,?\s*)?" + _WAKE + r"\b[\s,!.]*", "", t)
    prev = None
    while prev != t:
        prev = t
        t = re.sub(r"(?iu)[\s,]+" + _FILLER + r"[\s!?.]*$", "", t).strip()
    for a, b in _VOICE_FIX:
        if a in (r"\bpro\b",):  # "me leva pro X" ja e tratado pelo parser de rota; so troca fora dele
            continue
        t = re.sub(r"(?iu)" + a, b, t)
    return t


def gibberish(raw: str) -> bool:
    """Sem letras, letra repetida ("ãããã") ou so palavras impronunciaveis ("asdfgh qwerty")."""
    n = norm(raw)
    words = re.findall(r"[a-z]+", n)
    if not words:
        return True
    def bad(w):
        return ((len(set(w)) == 1 and len(w) > 1) or re.search(r"[^aeiou]{4,}", w) or (len(w) >= 5 and not re.search(r"[aeiou]", w))
                or re.search(r"qwe|wer|ert|rty|asd|sdf|dfg|fgh|ghj|hjk|jkl|zxc|xcv|cvb|vbn|bnm", w))
    return all(bad(w) for w in words) or (len(words) == 1 and len(words[0]) == 1 and words[0] not in "aeo")


def guard(raw: str):
    n = norm(raw)
    if not n:
        return None
    g = priority(raw)
    if g:
        return g
    if FALSE_CLAIM.fullmatch(n):
        return FALSE_CLAIM_REPLY
    m = CONTROL.fullmatch(n)
    if m:
        acao = re.sub(r"^(?:harumi |por favor )+", "", n).split(" ", 1)
        verbo = INFINITIVO.get(acao[0], acao[0])
        return CONTROL_REPLY.format(acao=(verbo + " " + acao[1]) if len(acao) > 1 else verbo)
    if READING.fullmatch(n):
        return READING_REPLY
    if SPEC.fullmatch(n):
        return SPEC_REPLY
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
