"""Garagem: abastecimentos (km/l), lembretes de manutencao e hodometro. Dados digitados pelo usuario, nada inventado.

Guarda em harumi_store: garage.fuel (lista), garage.maint (lista), garage.odo ({km, data}).
GET  /linux/garage      -> dados + calculos (km/l, vencimentos).
POST /linux/garage-add  {tipo: "fuel"|"maint"|"odo", ...campos}
POST /linux/garage-done {id, km?, data?}      marca a manutencao como feita agora (ou em km/data informados)
POST /linux/garage-del  {tipo: "fuel"|"maint", id}
Tudo e validado aqui; erro volta 400 com {ok:false, erro}.
Observacao: "hoje" vem do relogio da placa [VERIFICAR se o relogio do Orange Pi esta certo sem internet]."""
from __future__ import annotations

import calendar
import json
import re
import threading
import time
from datetime import date, datetime, timedelta

import harumi_store

K_FUEL, K_MAINT, K_ODO = "garage.fuel", "garage.maint", "garage.odo"
MAX_FUEL, MAX_MAINT = 2000, 50
MAX_KM, MAX_LITROS, MAX_VALOR = 2_000_000, 300.0, 10_000.0
_lock = threading.Lock()


class Erro(ValueError):
    pass


# ------------------------------------------------------------ validacao
def _num(v, nome, lo, hi, inteiro=False, opcional=False):
    if v is None or v == "":
        if opcional:
            return None
        raise Erro(f"{nome}: obrigatório")
    if isinstance(v, bool):
        raise Erro(f"{nome}: número inválido")
    try:
        x = float(str(v).replace(",", ".")) if isinstance(v, str) else float(v)
    except (TypeError, ValueError):
        raise Erro(f"{nome}: número inválido")
    if x != x or x in (float("inf"), float("-inf")) or not (lo < x <= hi):
        raise Erro(f"{nome}: deve ser maior que {lo:g} e no máximo {hi:g}")
    return int(round(x)) if inteiro else round(x, 3)


def _data(v, nome, opcional=False):
    if v is None or v == "":
        if opcional:
            return None
        raise Erro(f"{nome}: obrigatória")
    if not isinstance(v, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
        raise Erro(f"{nome}: use AAAA-MM-DD")
    try:
        d = datetime.strptime(v, "%Y-%m-%d").date()
    except ValueError:
        raise Erro(f"{nome}: data inexistente")
    if d.year < 1990 or d > date.today() + timedelta(days=366):
        raise Erro(f"{nome}: fora do intervalo razoável")
    return v


def _texto(v, nome, maxlen, opcional=False):
    if v is None or (isinstance(v, str) and not v.strip()):
        if opcional:
            return ""
        raise Erro(f"{nome}: obrigatório")
    if not isinstance(v, str):
        raise Erro(f"{nome}: texto inválido")
    t = " ".join(v.split())
    if len(t) > maxlen or re.search(r"[\x00-\x1f<>]", v.replace("\n", " ")):
        raise Erro(f"{nome}: até {maxlen} caracteres, sem < ou >")
    return t


def _id() -> int:
    return int(time.time() * 1000)


# ------------------------------------------------------------ calculos
def _add_months(d: date, n: int) -> date:
    m = d.month - 1 + n
    y, mo = d.year + m // 12, m % 12 + 1
    return date(y, mo, min(d.day, calendar.monthrange(y, mo)[1]))


def consumo(fuel: list) -> dict:
    """km/l pelo metodo do tanque cheio: entre dois abastecimentos 'cheio', km rodados / litros colocados
    desde o cheio anterior (incluindo o atual, excluindo o anterior). Parciais so somam litros."""
    ordenado = sorted(fuel, key=lambda f: f["km"])
    por_id, ult_cheio, litros_acum = {}, None, 0.0
    tot_km = tot_l = 0.0
    for f in ordenado:
        if ult_cheio is not None:
            litros_acum += f["litros"]
        if f.get("cheio"):
            if ult_cheio is not None and f["km"] > ult_cheio["km"] and litros_acum > 0:
                rodados = f["km"] - ult_cheio["km"]
                por_id[f["id"]] = round(rodados / litros_acum, 2)
                tot_km += rodados
                tot_l += litros_acum
            ult_cheio, litros_acum = f, 0.0
    media = round(tot_km / tot_l, 2) if tot_l > 0 else None
    return {"por_id": por_id, "media": media}


def vencimentos(maint: list, odo_km, hoje: date) -> list:
    out = []
    for m in maint:
        km_rest = dias_rest = None
        if m.get("cada_km") and m.get("ultimo_km") is not None and odo_km is not None:
            km_rest = int(m["ultimo_km"] + m["cada_km"] - odo_km)
        if m.get("cada_meses") and m.get("ultima_data"):
            alvo = _add_months(datetime.strptime(m["ultima_data"], "%Y-%m-%d").date(), m["cada_meses"])
            dias_rest = (alvo - hoje).days
        if km_rest is None and dias_rest is None:
            status = "sem_dados"
        elif (km_rest is not None and km_rest < 0) or (dias_rest is not None and dias_rest < 0):
            status = "vencido"
        elif (km_rest is not None and km_rest <= 500) or (dias_rest is not None and dias_rest <= 30):
            status = "atencao"
        else:
            status = "ok"
        out.append({**m, "km_restante": km_rest, "dias_restantes": dias_rest, "status": status})
    return out


def _estado() -> dict:
    fuel = harumi_store.get(K_FUEL, []) or []
    maint = harumi_store.get(K_MAINT, []) or []
    odo = harumi_store.get(K_ODO, None)
    kms = [f["km"] for f in fuel] + ([odo["km"]] if isinstance(odo, dict) and "km" in odo else [])
    odo_km = max(kms) if kms else None
    c = consumo(fuel)
    abast = []
    for f in sorted(fuel, key=lambda f: (f["data"], f["km"]), reverse=True):
        abast.append({**f, "kml": c["por_id"].get(f["id"]),
                      "preco_litro": round(f["valor"] / f["litros"], 3) if f["litros"] else None})
    return {"ok": True, "hoje": date.today().isoformat(), "odometro": odo_km, "media_kml": c["media"],
            "abastecimentos": abast, "manutencoes": vencimentos(maint, odo_km, date.today())}


# ------------------------------------------------------------ rotas
def _resp(status, obj):
    return status, "application/json", json.dumps(obj, ensure_ascii=False).encode()


def _get(query):
    return _resp(200, _estado())


def _guard(fn):
    def wrap(data):
        try:
            with _lock:
                fn(data)
            return _resp(200, _estado())
        except Erro as e:
            return _resp(400, {"ok": False, "erro": str(e)})
    return wrap


def _add(data):
    tipo = data.get("tipo")
    if tipo == "fuel":
        fuel = harumi_store.get(K_FUEL, []) or []
        if len(fuel) >= MAX_FUEL:
            raise Erro("limite de abastecimentos atingido")
        item = {"id": _id(), "data": _data(data.get("data"), "data"),
                "km": _num(data.get("km"), "km", 0, MAX_KM, inteiro=True),
                "litros": _num(data.get("litros"), "litros", 0, MAX_LITROS),
                "valor": _num(data.get("valor"), "valor", 0, MAX_VALOR),
                "posto": _texto(data.get("posto"), "posto", 40, opcional=True),
                "cheio": bool(data.get("cheio", True))}
        if any(f["km"] == item["km"] for f in fuel):
            raise Erro("já existe um abastecimento com esse km")
        fuel.append(item)
        harumi_store.set(K_FUEL, fuel)
    elif tipo == "maint":
        maint = harumi_store.get(K_MAINT, []) or []
        if len(maint) >= MAX_MAINT:
            raise Erro("limite de lembretes atingido")
        item = {"id": _id(), "nome": _texto(data.get("nome"), "nome", 40),
                "cada_km": _num(data.get("cada_km"), "a cada km", 0, 200_000, inteiro=True, opcional=True),
                "cada_meses": _num(data.get("cada_meses"), "a cada meses", 0, 120, inteiro=True, opcional=True),
                "ultimo_km": _num(data.get("ultimo_km"), "último km", -1, MAX_KM, inteiro=True, opcional=True),
                "ultima_data": _data(data.get("ultima_data"), "última data", opcional=True)}
        if not item["cada_km"] and not item["cada_meses"]:
            raise Erro("informe a cada quantos km e/ou meses")
        if item["cada_km"] and item["ultimo_km"] is None and not item["cada_meses"]:
            raise Erro("informe o km da última vez para calcular o vencimento")
        maint.append(item)
        harumi_store.set(K_MAINT, maint)
    elif tipo == "odo":
        harumi_store.set(K_ODO, {"km": _num(data.get("km"), "km", 0, MAX_KM, inteiro=True),
                                 "data": date.today().isoformat()})
    else:
        raise Erro("tipo inválido")


def _done(data):
    maint = harumi_store.get(K_MAINT, []) or []
    alvo = next((m for m in maint if m.get("id") == data.get("id")), None)
    if alvo is None:
        raise Erro("lembrete não encontrado")
    odo = harumi_store.get(K_ODO, None)
    fuel = harumi_store.get(K_FUEL, []) or []
    kms = [f["km"] for f in fuel] + ([odo["km"]] if isinstance(odo, dict) and "km" in odo else [])
    km = _num(data.get("km"), "km", -1, MAX_KM, inteiro=True, opcional=True)
    if km is None and kms:
        km = max(kms)  # hodometro conhecido mais recente
    alvo["ultimo_km"] = km
    alvo["ultima_data"] = _data(data.get("data"), "data", opcional=True) or date.today().isoformat()
    harumi_store.set(K_MAINT, maint)


def _del(data):
    tipo = data.get("tipo")
    chave = {"fuel": K_FUEL, "maint": K_MAINT}.get(tipo)
    if not chave:
        raise Erro("tipo inválido")
    lista = harumi_store.get(chave, []) or []
    nova = [x for x in lista if x.get("id") != data.get("id")]
    if len(nova) == len(lista):
        raise Erro("item não encontrado")
    harumi_store.set(chave, nova)


ROUTES = {"/linux/garage": _get}
POST_ROUTES = {"/linux/garage-add": _guard(_add), "/linux/garage-done": _guard(_done),
               "/linux/garage-del": _guard(_del)}
