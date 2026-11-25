import unittest
from pathlib import Path
from rdflib import Graph, Literal, RDF, RDFS

from src.knowledge_engine import FOOD, STANDARDS
from src.reasoner import DietaryReasoner


def _build_benchmark_graph() -> Graph:
    """Construct the 6 benchmark products from the specification matrix."""
    g = Graph()
    g.bind("food", FOOD)

    # Origins & Byproducts
    origins = [
        (FOOD.PorcineSrc, FOOD.Porcine),
        (FOOD.BovineSrc, FOOD.Bovine),
        (FOOD.InsectSrc, FOOD.Insect),
        (FOOD.PlantSrc, FOOD.PlantOrigin),
        (FOOD.MicrobialSrc, FOOD.MicrobialOrigin),
        (FOOD.SyntheticSrc, FOOD.SyntheticOrigin),
        (FOOD.DairySrc, FOOD.Dairy),
        (FOOD.HoneySrc, FOOD.Honey),
        (FOOD.EnzymeSrc, FOOD.AnimalEnzyme),
    ]
    for node, cls in origins:
        g.add((node, RDF.type, cls))

    # Certificates
    for cert in (FOOD.HalalCert01, FOOD.HalalCert02):
        g.add((cert, RDF.type, FOOD.HalalCert))
    for cert in (FOOD.KosherCert01, FOOD.KosherCert02):
        g.add((cert, RDF.type, FOOD.KosherCert))

    def add_ing(uri, label, source=None, role=None, ethanol=None, certs=()):
        g.add((uri, RDF.type, FOOD.Ingredient))
        g.add((uri, RDFS.label, Literal(label)))
        if source is not None:
            g.add((uri, FOOD.derivedFrom, source))
        if role is not None:
            g.add((role, RDF.type, FOOD.FunctionalRole))
            g.add((uri, FOOD.hasFunctionalRole, role))
        if ethanol is not None:
            g.add((uri, FOOD.ethanolPercentage, Literal(ethanol)))
        for c in certs:
            g.add((uri, FOOD.hasCertificate, c))

    # Ingredients catalog
    add_ing(FOOD.PorcineGelatin, "Porcine Gelatin", FOOD.PorcineSrc, FOOD.GellingAgent)
    add_ing(FOOD.AgarAgar, "Agar-Agar (E406)", FOOD.PlantSrc, FOOD.GellingAgent, certs=(FOOD.HalalCert01, FOOD.KosherCert01))
    add_ing(FOOD.Carmine, "Carmine (E120)", FOOD.InsectSrc, FOOD.Coloring)
    add_ing(FOOD.GlucoseSyrup, "Glucose Syrup", FOOD.PlantSrc)
    add_ing(FOOD.UncertBeefPatty, "Beef Patty", FOOD.BovineSrc)
    add_ing(FOOD.Cheddar, "Cheddar Cheese", FOOD.DairySrc)
    add_ing(FOOD.AnimalRennet, "Animal Rennet", FOOD.EnzymeSrc, FOOD.Coagulant)
    g.add((FOOD.Cheddar, FOOD.containsIngredient, FOOD.AnimalRennet))
    add_ing(FOOD.MicrobialRennet, "Microbial Rennet", FOOD.MicrobialSrc, FOOD.Coagulant, certs=(FOOD.HalalCert01, FOOD.KosherCert01))
    add_ing(FOOD.Flour, "Wheat Flour", FOOD.PlantSrc)
    add_ing(FOOD.Water, "Water", FOOD.SyntheticSrc)
    add_ing(FOOD.DoughConditioner, "Dough Conditioner")
    add_ing(FOOD.LCysteinePorcine, "L-Cysteine (E920)", FOOD.PorcineSrc, FOOD.DoughConditionerRole)
    g.add((FOOD.DoughConditioner, FOOD.containsIngredient, FOOD.LCysteinePorcine))
    add_ing(FOOD.MicrobialTG, "Microbial Transglutaminase", FOOD.MicrobialSrc, FOOD.DoughConditionerRole, certs=(FOOD.HalalCert01, FOOD.KosherCert01))
    add_ing(FOOD.Noodle, "Wheat Noodle", FOOD.PlantSrc)
    add_ing(FOOD.VegBroth, "Vegetable Broth", FOOD.PlantSrc)
    add_ing(FOOD.SoyLecithin, "Soy Lecithin (E322)", FOOD.PlantSrc, FOOD.Emulsifier, certs=(FOOD.HalalCert02, FOOD.KosherCert02))
    add_ing(FOOD.SweetWheyPowder, "Sweet Whey Powder", FOOD.DairySrc, FOOD.TextureEnhancer, certs=(FOOD.KosherCert01,))
    add_ing(FOOD.SoyProtein, "Soy Protein", FOOD.PlantSrc)
    add_ing(FOOD.RawHoney, "Honey", FOOD.HoneySrc)
    add_ing(FOOD.DairyButter, "Butter", FOOD.DairySrc, certs=(FOOD.KosherCert01,))
    add_ing(FOOD.VanillaExtract, "Vanilla Extract", FOOD.PlantSrc, FOOD.Flavoring, ethanol=1.2)
    add_ing(FOOD.SyntheticVanilla, "Synthetic Vanilla", FOOD.SyntheticSrc, FOOD.Flavoring, ethanol=0.0, certs=(FOOD.HalalCert01,))

    def add_prod(uri, label, *ings):
        g.add((uri, RDF.type, FOOD.FoodProduct))
        g.add((uri, RDFS.label, Literal(label)))
        for ing in ings:
            g.add((uri, FOOD.containsIngredient, ing))

    # 1. Strawberry Gummy Candy: Fail, Fail, Fail, Fail
    add_prod(FOOD.StrawberryGummyCandy, "Strawberry Gummy Candy",
             FOOD.PorcineGelatin, FOOD.Carmine, FOOD.GlucoseSyrup)

    # 2. Beef Cheese Burger (with uncertified beef + cheddar w/ animal rennet): Audit, Fail, Fail, Fail
    add_prod(FOOD.BeefCheeseBurger, "Beef Cheese Burger",
             FOOD.UncertBeefPatty, FOOD.Cheddar, FOOD.Flour)

    # 3. Artisan Dough Bread (3-level nested porcine L-Cysteine): Fail, Fail, Fail, Fail
    add_prod(FOOD.ArtisanDoughBread, "Artisan Dough Bread",
             FOOD.Flour, FOOD.Water, FOOD.DoughConditioner)

    # 4. Plant-Based Ramen: Pass, Pass, Pass, Pass
    add_prod(FOOD.PlantBasedRamen, "Plant-Based Ramen",
             FOOD.Noodle, FOOD.VegBroth, FOOD.AgarAgar, FOOD.SoyLecithin)

    # 5. Whey Protein Bar: Pass, Pass, Pass, Fail (Honey & Dairy)
    add_prod(FOOD.WheyProteinBar, "Whey Protein Bar",
             FOOD.SweetWheyPowder, FOOD.SoyProtein, FOOD.RawHoney)

    # 6. Vanilla Pastry: Fail (Ethanol > 0.5%), Pass, Pass, Fail (Dairy)
    add_prod(FOOD.VanillaPastry, "Vanilla Pastry",
             FOOD.Flour, FOOD.DairyButter, FOOD.VanillaExtract)

    return g


class DietaryReasonerTests(unittest.TestCase):
    def setUp(self):
        self.graph = _build_benchmark_graph()
        self.reasoner = DietaryReasoner(self.graph)

    def test_benchmark_products_produce_expected_compliance_matrix(self):
        expected = {
            FOOD.StrawberryGummyCandy: ("Fail", "Fail", "Fail", "Fail"),
            FOOD.BeefCheeseBurger: ("Audit Required", "Fail", "Fail", "Fail"),
            FOOD.ArtisanDoughBread: ("Fail", "Fail", "Fail", "Fail"),
            FOOD.PlantBasedRamen: ("Pass", "Pass", "Pass", "Pass"),
            FOOD.WheyProteinBar: ("Pass", "Pass", "Pass", "Fail"),
            FOOD.VanillaPastry: ("Fail", "Pass", "Pass", "Fail"),
        }
        for product, exp_statuses in expected.items():
            with self.subTest(product=product):
                report = self.reasoner.evaluate_product(product)
                actual = tuple(report[std]["status"] for std in STANDARDS)
                self.assertEqual(actual, exp_statuses)

    def test_materializes_is_compliant_with_and_substitutes_in_enriched_graph(self):
        enriched = self.reasoner.materialize()
        self.assertIn((FOOD.PlantBasedRamen, FOOD.isCompliantWith, FOOD.Halal), enriched)
        self.assertIn((FOOD.PlantBasedRamen, FOOD.isCompliantWith, FOOD.Kosher), enriched)
        self.assertIn((FOOD.PlantBasedRamen, FOOD.isCompliantWith, FOOD.Vegetarian), enriched)
        self.assertIn((FOOD.PlantBasedRamen, FOOD.isCompliantWith, FOOD.Vegan), enriched)
        self.assertIn((FOOD.PorcineGelatin, FOOD.hasSuggestedSubstitute, FOOD.AgarAgar), enriched)
        self.assertIn((FOOD.VanillaExtract, FOOD.hasSuggestedSubstitute, FOOD.SyntheticVanilla), enriched)

    def test_unverified_leaf_ingredient_without_origin_requires_audit(self):
        g = Graph()
        g.add((FOOD.MysteryMeal, RDF.type, FOOD.FoodProduct))
        g.add((FOOD.MysteryMeal, FOOD.containsIngredient, FOOD.UnknownPowder))
        g.add((FOOD.UnknownPowder, RDF.type, FOOD.Ingredient))
        reasoner = DietaryReasoner(g)
        report = reasoner.evaluate_product(FOOD.MysteryMeal)
        for std in STANDARDS:
            self.assertEqual(report[std]["status"], "Audit Required")
            self.assertTrue(any("missing biological origin" in iss["message"].lower() for iss in report[std]["issues"]))

    def test_from_default_files_loads_project_ontologies(self):
        reasoner = DietaryReasoner.from_default_files()
        self.assertGreaterEqual(len(reasoner.products()), 6)


if __name__ == "__main__":
    unittest.main()
