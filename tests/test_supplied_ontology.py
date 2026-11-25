import unittest
from pathlib import Path

from src.knowledge_engine import FOOD, KnowledgeEngine


ROOT = Path(__file__).resolve().parents[1] / "ontology"


class SuppliedOntologyTests(unittest.TestCase):
    def test_loads_products_and_detects_nested_and_ethanol_issues(self):
        engine = KnowledgeEngine.from_turtle(
            ROOT / "food_compliance_tbox.ttl", ROOT / "food_compliance_abox.ttl"
        )
        self.assertEqual(len(engine.products()), 6)
        self.assertEqual(len(engine.ingredients()), 24)
        bread = engine.evaluate(FOOD.ArtisanSourdoughBread)
        self.assertEqual(bread[FOOD.Halal]["status"], "Fail")
        self.assertTrue(any(FOOD.LCysteine_E920 in issue["ingredients"]
                            for issue in bread[FOOD.Halal]["issues"]))
        pastry = engine.evaluate(FOOD.VanillaCreamPastry)
        self.assertTrue(any(FOOD.NaturalVanillaExtract in issue["ingredients"]
                            for issue in pastry[FOOD.Halal]["issues"]))
