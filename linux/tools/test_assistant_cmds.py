"""Autoteste dos comandos locais da Harumi (T5). Uso: python tools/test_assistant_cmds.py"""
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import harumi_assistant as ha  # noqa: E402

CASES = [
    # (frase, esperado) ; None = NAO e comando novo (nao pode virar VOLUME/OPEN_APP/CLOSE_APP/CLOCK/ETA/CLEAN)
    ("aumenta o volume", ("VOLUME", ("step", 10))),
    ("Aumenta o volume, por favor", ("VOLUME", ("step", 10))),
    ("Harumi, aumenta o volume", ("VOLUME", ("step", 10))),
    ("sobe o volume um pouco", ("VOLUME", ("step", 5))),
    ("pode abaixar o volume", ("VOLUME", ("step", -10))),
    ("abaixa o volume", ("VOLUME", ("step", -10))),
    ("diminui o som um pouco", ("VOLUME", ("step", -5))),
    ("volume em 30", ("VOLUME", ("set", 30))),
    ("coloca o volume em 50%", ("VOLUME", ("set", 50))),
    ("deixa o volume para 80 por cento", ("VOLUME", ("set", 80))),
    ("silencia", ("VOLUME", ("mute", True))),
    ("silencia o som", ("VOLUME", ("mute", True))),
    ("tira o mudo", ("VOLUME", ("mute", False))),
    ("desmuta", ("VOLUME", ("mute", False))),
    ("abre o waze", ("OPEN_APP", "waze")),
    ("abre o Claude", ("OPEN_APP", "claude")),
    ("abre o ChatGPT", ("OPEN_APP", "chatgpt")),
    ("abre o chat gpt", ("OPEN_APP", "chatgpt")),
    ("abra o navegador de internet", ("OPEN_APP", "browser")),
    ("abre o YouTube", ("YOUTUBE", "")),
    ("abre o spotify", ("MUSIC", "")),
    ("abre o mapa", ("MAP", "")),
    ("fecha o app", ("CLOSE_APP", "")),
    ("fechar a janela", ("CLOSE_APP", "")),
    ("que horas são", ("CLOCK", "")),
    ("Que horas sao?", ("CLOCK", "")),
    ("quanto falta?", ("ETA", "")),
    ("quando chego", ("ETA", "")),
    ("modo tela limpa", ("CLEAN", True)),
    ("ativa o modo tela limpa", ("CLEAN", True)),
    ("sair da tela limpa", ("CLEAN", False)),
    ("desativa o modo tela limpa", ("CLEAN", False)),
    # negativas: perguntas e frases longas nao viram comando
    ("o que é volume morto?", None),
    ("por que o volume do rádio do meu carro some quando eu freio?", None),
    ("como faço para aumentar o volume do meu cachorro latindo", None),
    ("o que é modo tela limpa?", None),
    ("volume em 300", None),
    ("que horas o posto abre na estrada?", None),
    ("quanto falta de óleo no motor?", None),
    ("explica o que é o Waze", None),
    ("fecha o assunto, por favor, e me conta como funciona o freio", None),
    ("o claude é melhor que o chatgpt?", None),
]
NEW = {"VOLUME", "OPEN_APP", "CLOSE_APP", "CLOCK", "ETA", "CLEAN"}


def main() -> int:
    bad = 0
    for text, want in CASES:
        got = ha.parse(text)
        ok = (got == want) if want is not None else (got[0] not in NEW)
        if not ok:
            bad += 1
            print(f"FALHOU: {text!r} -> {got!r} (esperado {want!r})")
    # respostas puras
    t = [
        (ha.clock_reply(datetime(2026, 11, 16, 14, 5)) == "Agora são 14h05."),
        (ha.clock_reply(datetime(2026, 11, 16, 9, 0)) == "São 9 horas em ponto."),
        ("Não há rota ativa" in ha.eta_reply(None)),
        ("Não há rota ativa" in ha.eta_reply({"distance": 0})),
        ("12,3 km" in ha.eta_reply({"distance": 12345})),
        ("cerca de 1h30" in ha.eta_reply({"distance": 100000, "duration": 5400})),
    ]
    for i, ok in enumerate(t):
        if not ok:
            bad += 1
            print("FALHOU resposta pura", i)
    print(f"{len(CASES)} frases + {len(t)} respostas; falhas: {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
