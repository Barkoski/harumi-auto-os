"""Rota offline: GraphHopper 11.1 local (servico harumi-routes, 127.0.0.1:8989) com o grafo do Brasil.

A interface (road-map.js) foi feita para a resposta do OSRM; aqui a resposta do GraphHopper vira o mesmo formato:
routes[0].{distance, duration, geometry{coordinates}, legs[0].steps[{distance, duration, name, geometry, maneuver{type,
modifier, location, bearing_after, exit}}]}. Sem o servico local, devolve None e o servidor segue para o OSRM online.
Codigos de "sign" do GraphHopper (classe Instruction): -98/-8/8 retorno, -7/7 manter esquerda/direita, -6 sair da rotatoria,
-3/-2/-1 esquerda forte/esquerda/leve, 0 seguir, 1/2/3 direita leve/direita/forte, 4 chegada, 5 ponto intermediario,
6 rotatoria. [VERIFICAR contra a versao 11.1 se aparecer manobra estranha na tela]
"""
from __future__ import annotations

import json
import math
import urllib.parse
import urllib.request

GH_URL = "http://127.0.0.1:8989/route"
TIMEOUT = 8

_MOD = {-3: "sharp left", -2: "left", -1: "slight left", 1: "slight right", 2: "right", 3: "sharp right"}


def _bearing(a, b) -> int:
    lon1, lat1, lon2, lat2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    y = math.sin(lon2 - lon1) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(lon2 - lon1)
    return int((math.degrees(math.atan2(y, x)) + 360) % 360)


def _maneuver(sign: int, first: bool, exit_number):
    if first:
        return {"type": "depart"}
    if sign == 4:
        return {"type": "arrive"}
    if sign == 5:
        return {"type": "notification"}
    if sign == 6:
        m = {"type": "roundabout"}
        if isinstance(exit_number, int) and exit_number > 0:
            m["exit"] = exit_number
        return m
    if sign == -6:
        return {"type": "exit roundabout"}
    if sign in (-98, -8, 8):
        return {"type": "turn", "modifier": "uturn"}
    if sign == -7:
        return {"type": "fork", "modifier": "slight left"}
    if sign == 7:
        return {"type": "fork", "modifier": "slight right"}
    if sign == 0:
        return {"type": "continue", "modifier": "straight"}
    if sign in _MOD:
        return {"type": "turn", "modifier": _MOD[sign]}
    return {"type": "continue", "modifier": "straight"}


def to_osrm(gh: dict) -> dict | None:
    paths = gh.get("paths") or []
    if not paths:
        return None
    p = paths[0]
    coords = (p.get("points") or {}).get("coordinates") or []
    if len(coords) < 2:
        return None
    steps = []
    for i, ins in enumerate(p.get("instructions") or []):
        a, b = (ins.get("interval") or [0, 0])[:2]
        seg = coords[a:b + 1] or [coords[a]]
        man = _maneuver(int(ins.get("sign", 0)), i == 0, ins.get("exit_number"))
        man["location"] = coords[a]
        if len(seg) > 1:
            man["bearing_after"] = _bearing(seg[0], seg[1])
        steps.append({"distance": ins.get("distance", 0), "duration": (ins.get("time") or 0) / 1000.0,
                      "name": ins.get("street_name") or "", "mode": "driving", "maneuver": man,
                      "geometry": {"type": "LineString", "coordinates": seg},
                      "intersections": [{"location": coords[a]}]})
    dist, dur = p.get("distance", 0), (p.get("time") or 0) / 1000.0
    route = {"distance": dist, "duration": dur, "weight": dur, "weight_name": "routability",
             "geometry": {"type": "LineString", "coordinates": coords},
             "legs": [{"distance": dist, "duration": dur, "summary": "", "steps": steps}]}
    return {"code": "Ok", "routes": [route], "waypoints": [{"location": coords[0]}, {"location": coords[-1]}],
            "engine": "graphhopper-local"}


def local_route(osrm_path: str) -> dict | None:
    """osrm_path = 'lon,lat;lon,lat' (ja validado por route_points). None se o servico local nao responder."""
    try:
        (lon1, lat1), (lon2, lat2) = [tuple(float(v) for v in p.split(",")) for p in osrm_path.split(";")]
    except ValueError:
        return None
    q = urllib.parse.urlencode([("point", f"{lat1:.6f},{lon1:.6f}"), ("point", f"{lat2:.6f},{lon2:.6f}"),
                                ("profile", "car"), ("locale", "pt_BR"), ("instructions", "true"),
                                ("points_encoded", "false"), ("calc_points", "true")])
    try:
        with urllib.request.urlopen(GH_URL + "?" + q, timeout=TIMEOUT) as r:
            gh = json.loads(r.read(8 * 1024 * 1024).decode("utf-8"))
    except (OSError, ValueError):
        return None
    return to_osrm(gh)
