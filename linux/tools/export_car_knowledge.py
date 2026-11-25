#!/usr/bin/env python3
"""Exporta as respostas conferidas do Android (CarKnowledge.java + QuickReplies) para linux/car_knowledge.json.
Fonte unica: o arquivo Java. Rodar de novo sempre que ele mudar:
    python linux/tools/export_car_knowledge.py
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "app/src/main/java/com/harumi/autoos/ai/CarKnowledge.java"
OUT = ROOT / "linux/car_knowledge.json"


def java_str(s):
    """Desfaz o escape de string Java (\\\\ -> \\, \\" -> ")."""
    return re.sub(r'\\(["\\])', r"\1", s)


def main():
    src = SRC.read_text(encoding="utf-8")
    entries = []
    for m in re.finditer(r'K\("(\w+)",\s*"((?:[^"\\]|\\.)*)",\s*"((?:[^"\\]|\\.)*)"\)', src, re.S):
        entries.append({"id": m.group(1), "regex": java_str(m.group(2)), "answer": java_str(m.group(3))})

    def table(name):
        block = re.search(name + r"\s*=\s*\{(.*?)\};", src, re.S).group(1)
        rows = []
        for r in re.finditer(r'\{"(\d{2})",\s*"((?:[^"\\]|\\.)*)"(?:,\s*(true|false))?\}', block):
            rows.append({"code": r.group(1), "text": java_str(r.group(2)), "singleSource": r.group(3) == "true"})
        return rows

    data = {"source": "app/src/main/java/com/harumi/autoos/ai/CarKnowledge.java", "entries": entries,
            "engine": table("ENGINE"), "gearbox": table("GEAR")}
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(entries)} respostas, {len(data['engine'])} codigos de motor, {len(data['gearbox'])} de cambio -> {OUT}")


if __name__ == "__main__":
    main()
