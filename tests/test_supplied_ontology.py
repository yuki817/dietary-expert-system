import unittest
from pathlib import Path

from src.knowledge_engine import FOOD, KnowledgeEngine
from src.reasoner import DietaryReasoner


ROOT = Path(__file__).resolve().parents[1] / "ontology"


class SuppliedOntologyTests(unittest.TestCase):
    def test_loads_products_and_detects_nested_and_ethanol_issues(self):
        engine = KnowledgeEngine.from_turtle(
            ROOT / "food_compliance_tbox.ttl", ROOT / "food_compliance_abox.ttl"
        )
        self.assertEqual(len(engine.products()), 10)
        self.assertEqual(len(engine.ingredients()), 34)
        bread = engine.evaluate(FOOD.ArtisanSourdoughBread)
        self.assertEqual(bread[FOOD.Halal]["status"], "Fail")
        self.assertTrue(any(FOOD.LCysteine_E920 in issue["ingredients"]
                            for issue in bread[FOOD.Halal]["issues"]))
        pastry = engine.evaluate(FOOD.VanillaCreamPastry)
        self.assertTrue(any(FOOD.NaturalVanillaExtract in issue["ingredients"]
                            for issue in pastry[FOOD.Halal]["issues"]))

    def test_meat_milk_haram_and_halal_initial_data(self):
        engine = KnowledgeEngine.from_turtle(
            ROOT / "food_compliance_tbox.ttl", ROOT / "food_compliance_abox.ttl"
        )
        reasoner = DietaryReasoner(engine.graph)

        # Clearly Halal meat & dairy product (Meat + Milk): Halal Pass, Kosher Fail (meat+dairy), Veg/Vegan Fail
        alfredo = reasoner.evaluate_product(FOOD.CreamyChickenAlfredoPasta)
        self.assertEqual(alfredo[FOOD.Halal]["status"], "Pass")
        self.assertEqual(alfredo[FOOD.Kosher]["status"], "Fail")
        self.assertEqual(alfredo[FOOD.Vegetarian]["status"], "Fail")
        self.assertEqual(alfredo[FOOD.Vegan]["status"], "Fail")

        # Pure Milk-based product: Halal/Kosher/Vegetarian Pass, Vegan Fail
        ice_cream = reasoner.evaluate_product(FOOD.ClassicMilkIceCream)
        self.assertEqual(ice_cream[FOOD.Halal]["status"], "Pass")
        self.assertEqual(ice_cream[FOOD.Kosher]["status"], "Pass")
        self.assertEqual(ice_cream[FOOD.Vegetarian]["status"], "Pass")
        self.assertEqual(ice_cream[FOOD.Vegan]["status"], "Fail")

        # Halal Certified Beef Steak Bowl: Halal Pass, Kosher/Veg/Vegan Fail
        steak = reasoner.evaluate_product(FOOD.HalalBeefSteakBowl)
        self.assertEqual(steak[FOOD.Halal]["status"], "Pass")
        self.assertEqual(steak[FOOD.Kosher]["status"], "Fail")
        self.assertEqual(steak[FOOD.Vegetarian]["status"], "Fail")
        self.assertEqual(steak[FOOD.Vegan]["status"], "Fail")

        # Clearly Haram product (Pork Bacon + Pork Lard + Red Wine 12.5% alcohol): Fails all 4 standards
        haram_stew = reasoner.evaluate_product(FOOD.PorkWineBraisedStew)
        for std in (FOOD.Halal, FOOD.Kosher, FOOD.Vegetarian, FOOD.Vegan):
            self.assertEqual(haram_stew[std]["status"], "Fail")
        halal_flagged = {
            ing
            for issue in haram_stew[FOOD.Halal]["issues"]
            for ing in issue["ingredients"]
        }
        self.assertIn(FOOD.PorkBaconBits, halal_flagged)
        self.assertIn(FOOD.PorcineLard, halal_flagged)
        self.assertIn(FOOD.CookingRedWine, halal_flagged)
