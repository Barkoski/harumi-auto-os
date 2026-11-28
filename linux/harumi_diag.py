"""Diagnostico por conversa: o motorista descreve o sintoma, a Harumi pergunta detalhes e chega as causas provaveis.

As arvores ficam em diagnostico/arvores.json (editavel sem mexer em codigo). Cada arvore:
  {"id", "titulo", "gatilho": regex (texto normalizado), "inicio": no,
   "nos": {no: {"pergunta", "opcoes": [{"chaves": [regex...], "vai": no}], "nao_sei": no}
           | {"causas", "conferir", "rodar", "fonte"}}}
Conhecimento: mecanica geral de carros + o que a base do Impreza (docs/subaru) confirma. Nada aqui e diagnostico
definitivo: a resposta sempre diz o que conferir e se da para rodar.

API:
  start(texto) -> (resposta, estado) ou None
  answer(estado, texto) -> (resposta, estado_novo_ou_None) ou None (resposta nao reconhecida duas vezes: sai)
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

ARQ = Path(__file__).resolve().parent / "diagnostico" / "arvores.json"
SAIR = re.compile(r"(?:sair|sai|cancela\w*|esquece|chega|deixa pra la|para|pare|parar|tchau|depois eu vejo|nao quero mais)"
                  r"(?: (?:isso|o diagnostico|disso))?")
NAO_SEI = re.compile(r".*\b(?:nao sei|nao reparei|nao percebi|sei la|nao lembro|talvez|nao tenho certeza|nao sei dizer)\b.*")


def norm(s: str) -> str:
    s = "".join(c for c in unicodedata.normalize("NFD", s or "") if unicodedata.category(c) != "Mn").lower()
    return re.sub(r"\s+", " ", re.sub(r"[,.!?;:\"'()]", " ", s)).strip()


def _load():
    try:
        data = json.loads(ARQ.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    trees = []
    for t in data.get("arvores", []):
        try:
            t["_rx"] = re.compile(t["gatilho"])
            for no in t["nos"].values():
                for op in no.get("opcoes", []):
                    op["_rx"] = [re.compile(r"(?:^|.*\b)(?:" + c + r")\b.*") for c in op["chaves"]]
        except (KeyError, re.error):
            continue
        trees.append(t)
    return trees


TREES = _load()
BY_ID = {t["id"]: t for t in TREES}


def _ask(no: dict) -> str:
    return no["pergunta"]


def _leaf(t: dict, no: dict) -> str:
    partes = [no["causas"]]
    if no.get("conferir"):
        partes.append(no["conferir"])
    if no.get("rodar"):
        partes.append(no["rodar"])
    return " ".join(partes)


def _goto(t: dict, key: str):
    no = t["nos"][key]
    if "pergunta" in no:
        return _ask(no), {"arvore": t["id"], "no": key, "erros": 0}
    return _leaf(t, no), None


_NEG = re.compile(r"(?:^|.*\b)(?:nao|nunca|nem)\b.*")


def _match(no: dict, n: str):
    """Opcao escolhida. Resposta negativa ("nao ouvi nada") procura primeiro a opcao do "nao", senao "ouvi" viraria sim."""
    ops = no.get("opcoes", [])
    if _NEG.fullmatch(n):
        ops = sorted(ops, key=lambda op: 0 if "nao" in op["chaves"] else 1)
    for op in ops:
        if any(rx.fullmatch(n) for rx in op["_rx"]):
            return op
    return None


def start(texto: str):
    n = norm(texto)
    for t in TREES:
        if t["_rx"].fullmatch(n):
            intro = t.get("intro", "Vamos descobrir juntos.")
            key = t["inicio"]
            # Se a frase inicial ja responde a primeira pergunta ("tac tac", "embreagem patinando"), pula ela
            primeiro = t["nos"][key]
            if "pergunta" in primeiro and not _NEG.fullmatch(n):
                op = _match(primeiro, n)
                if op:
                    key = op["vai"]
            resp, st = _goto(t, key)
            return f"{intro} {resp}", st
    return None


def answer(estado: dict, texto: str):
    t = BY_ID.get((estado or {}).get("arvore"))
    if not t:
        return None
    no = t["nos"].get(estado.get("no"), {})
    n = norm(texto)
    if SAIR.fullmatch(n):
        return "Tudo bem, parei o diagnóstico. Se o problema voltar, é só me contar.", None
    if NAO_SEI.fullmatch(n) and no.get("nao_sei"):  # antes das opcoes: "nao sei" nao pode virar "nao"
        return _goto(t, no["nao_sei"])
    op = _match(no, n)
    if op:
        return _goto(t, op["vai"])
    erros = estado.get("erros", 0) + 1
    if erros >= 2:
        return None  # nao entendeu duas vezes: sai do diagnostico e deixa o assistente tratar a frase
    dica = no.get("dica") or "Pode responder com sim, não ou não sei."
    return f"Não entendi. {dica} {_ask(no)}", dict(estado, erros=erros)
