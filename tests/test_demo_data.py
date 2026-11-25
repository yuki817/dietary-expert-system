import unittest
from pathlib import Path

from src.knowledge_engine import FOOD, STANDARDS, KnowledgeEngine
from src.reformulation import candidates, simulate


ROOT = Path(__file__).resolve().parents[1] / "ontology"


class DemoDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = KnowledgeEngine.from_turtle(
            ROOT / "sample_tbox.ttl", ROOT / "sample_abox.ttl", ROOT / "demo_abox.ttl"
        )

    def test_demo_scenarios_show_expected_provisional_results(self):
        expected = {
            FOOD.DemoCandy: ("Fail", "Fail", "Not assessed", "Not assessed"),
            FOOD.DemoBeefProduct: ("Audit Required", "Not assessed", "Fail", "Fail"),
            FOOD.DemoCheeseburger: ("Not assessed", "Fail", "Fail", "Fail"),
            FOOD.DemoPastry: ("Fail", "Not assessed", "Not assessed", "Not assessed"),
            FOOD.DemoPlantProduct: ("Not assessed",) * 4,
        }
        for product, statuses in expected.items():
            with self.subTest(product=product):
                result = self.engine.evaluate(product)
                self.assertEqual(tuple(result[standard]["status"] for standard in STANDARDS), statuses)

    def test_demo_candy_can_be_simulated_with_agar(self):
        matches = candidates(self.engine, FOOD.DemoPorkGelatin, [FOOD.Halal, FOOD.Kosher])
        self.assertIn(FOOD.DemoAgar, [match[0] for match in matches])
        result = simulate(self.engine, FOOD.DemoCandy, FOOD.DemoPorkGelatin, FOOD.DemoAgar)
        self.assertEqual(result[FOOD.Halal]["status"], "Not assessed")
        self.assertEqual(result[FOOD.Kosher]["status"], "Not assessed")
