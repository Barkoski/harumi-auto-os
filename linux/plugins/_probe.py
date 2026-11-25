"""Sonda de teste (so carrega com HARUMI_PROBE=1)."""
import json
import time

import harumi_store


def _probe(query):
    harumi_store.set("probe", {"t": int(time.time())})
    return 200, "application/json", json.dumps({"ok": True, "store": harumi_store.get("probe")}).encode()


def _post(data):
    return 200, "application/json", json.dumps({"ok": True, "eco": data.get("x")}).encode()


def _action(module, emit):
    return [{"fn": "__notify", "args": ["Sonda: " + module]}]


ROUTES = {"/linux/probe": _probe}
POST_ROUTES = {"/linux/probe-post": _post}
ACTIONS = {"probe.ping": _action}
