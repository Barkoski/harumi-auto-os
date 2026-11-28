import importlib.util
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'linux'))  # harumi_assistant importa harumi_diag (diagnostico por conversa)
sys.modules.setdefault('harumi_guard', types.ModuleType('harumi_guard'))
spec = importlib.util.spec_from_file_location('harumi_assistant', ROOT / 'linux/harumi_assistant.py')
assistant = importlib.util.module_from_spec(spec)
spec.loader.exec_module(assistant)

class Regression(unittest.TestCase):
    def test_queries(self):
        cases = {
            'Qual óleo do câmbio manual?': 'óleo de engrenagens',
            'Quantos litros de óleo vai no câmbio?': 'quantidade',
            'O carro trepida nas curvas fechadas': 'awd manual',
            'Qual óleo do diferencial traseiro?': 'diferencial traseiro',
            'Qual embreagem comprar?': 'acionamento',
            'código 24 do câmbio': 'caixa atual é manual',
            'Fusível FWD': 'histórico',
            'A luz AT OIL TEMP acendeu': 'swap manual',
            'Como rebocar em pane?': 'guincho plataforma',
        }
        for question, expected in cases.items():
            with self.subTest(question=question):
                answer = assistant.car_answer(question)
                self.assertIsNotNone(answer)
                self.assertIn(expected, answer.lower())
        self.assertEqual([], assistant.GEAR_CODES)

if __name__ == '__main__': unittest.main()
