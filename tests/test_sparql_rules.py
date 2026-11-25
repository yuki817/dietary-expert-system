import unittest
from pathlib import Path
from rdflib import Graph, Literal, RDF, RDFS

from src.knowledge_engine import FOOD


RULES_DIR = Path(__file__).resolve().parents[1] / "rules"


def _run_rule(graph: Graph, rule_filename: str) -> Graph:
    query_text = (RULES_DIR / rule_filename).read_text(encoding="utf-8")
    result = graph.query(query_text)
    inferred = Graph()
    for triple in result.graph:
        inferred.add(triple)
    return inferred


class SparqlRulesTests(unittest.TestCase):
    def test_kosher_rule_flags_porcine_marine_insect_and_uncertified_animal(self):
        graph = Graph()
        for prod, ing, src, src_type in [
            (FOOD.P1, FOOD.PorkIng, FOOD.PorkSrc, food_kind := FOOD.Porcine),
            (FOOD.P2, FOOD.ShellfishIng, FOOD.MarineSrc, FOOD.Marine),
            (FOOD.P3, FOOD.CarmineIng, FOOD.InsectSrc, FOOD.Insect),
            (FOOD.P4, FOOD.UncertBeef, FOOD.BeefSrc, FOOD.Bovine),
        ]:
            graph.add((prod, RDF.type, FOOD.FoodProduct))
            graph.add((prod, FOOD.containsIngredient, ing))
            graph.add((ing, FOOD.derivedFrom, src))
            graph.add((src, RDF.type, src_type))

        # Certified dairy product should NOT fail kosher.sparql
        graph.add((FOOD.P5, RDF.type, FOOD.FoodProduct))
        graph.add((FOOD.P5, FOOD.containsIngredient, FOOD.CertWhey))
        graph.add((FOOD.CertWhey, FOOD.derivedFrom, FOOD.DairySrc))
        graph.add((FOOD.DairySrc, RDF.type, FOOD.Dairy))
        graph.add((FOOD.CertWhey, FOOD.hasCertificate, FOOD.KCert1))
        graph.add((FOOD.KCert1, RDF.type, FOOD.KosherCert))

        inferred = _run_rule(graph, "kosher.sparql")
        for prod in (FOOD.P1, FOOD.P2, FOOD.P3, FOOD.P4):
            self.assertIn((prod, FOOD.isNonCompliantWith, FOOD.Kosher), inferred)
        self.assertNotIn((FOOD.P5, FOOD.isNonCompliantWith, FOOD.Kosher), inferred)

    def test_kosher_rule_flags_meat_and_dairy_including_cheese(self):
        graph = Graph()
        graph.add((FOOD.Burger, RDF.type, FOOD.FoodProduct))
        graph.add((FOOD.Burger, FOOD.containsIngredient, FOOD.BeefPatty))
        graph.add((FOOD.BeefPatty, FOOD.derivedFrom, FOOD.BovineSrc))
        graph.add((FOOD.BovineSrc, RDF.type, FOOD.Bovine))
        graph.add((FOOD.BeefPatty, FOOD.hasCertificate, FOOD.KCert))
        graph.add((FOOD.KCert, RDF.type, FOOD.KosherCert))

        graph.add((FOOD.Burger, FOOD.containsIngredient, FOOD.Cheddar))
        graph.add((FOOD.Cheddar, FOOD.derivedFrom, FOOD.CheeseSrc))
        graph.add((FOOD.CheeseSrc, RDF.type, FOOD.Cheese))
        graph.add((FOOD.Cheddar, FOOD.hasCertificate, FOOD.KCert))

        inferred = _run_rule(graph, "kosher.sparql")
        self.assertIn((FOOD.Burger, FOOD.isNonCompliantWith, FOOD.Kosher), inferred)
        issues = list(inferred.objects(FOOD.Burger, FOOD.hasIssue))
        self.assertEqual(len(issues), 1)
        flagged = set(inferred.objects(issues[0], FOOD.flaggedIngredient))
        self.assertEqual(flagged, {FOOD.BeefPatty, FOOD.Cheddar})

    def test_vegan_veg_rule_covers_all_animal_origins_and_byproducts(self):
        graph = Graph()
        # Porcine gelatin (Porcine without MeatTissue) -> fails Vegetarian AND Vegan
        graph.add((FOOD.Candy, RDF.type, FOOD.FoodProduct))
        graph.add((FOOD.Candy, FOOD.containsIngredient, FOOD.Gelatin))
        graph.add((FOOD.Gelatin, FOOD.derivedFrom, FOOD.PorkSrc))
        graph.add((FOOD.PorkSrc, RDF.type, FOOD.Porcine))

        # Honey product -> passes Vegetarian (no failure), fails Vegan
        graph.add((FOOD.Bar, RDF.type, FOOD.FoodProduct))
        graph.add((FOOD.Bar, FOOD.containsIngredient, FOOD.HoneyIng))
        graph.add((FOOD.HoneyIng, FOOD.derivedFrom, FOOD.HoneySrc))
        graph.add((FOOD.HoneySrc, RDF.type, FOOD.Honey))

        inferred = _run_rule(graph, "vegan_veg.sparql")
        self.assertIn((FOOD.Candy, FOOD.isNonCompliantWith, FOOD.Vegetarian), inferred)
        self.assertIn((FOOD.Candy, FOOD.isNonCompliantWith, FOOD.Vegan), inferred)
        self.assertNotIn((FOOD.Bar, FOOD.isNonCompliantWith, FOOD.Vegetarian), inferred)
        self.assertIn((FOOD.Bar, FOOD.isNonCompliantWith, FOOD.Vegan), inferred)
        for issue in inferred.subjects(RDF.type, FOOD.ComplianceIssue):
            msg = str(inferred.value(issue, RDFS.label))
            self.assertNotIn("http://example.org/food-compliance#", msg)

    def test_substitution_rules_construct_valid_plant_microbial_synthetic_alternatives(self):
        graph = Graph()
        # Flagged porcine gelatin
        graph.add((FOOD.PorcineGelatin, RDF.type, FOOD.Ingredient))
        graph.add((FOOD.PorcineGelatin, FOOD.hasFunctionalRole, FOOD.GellingAgent))
        graph.add((FOOD.PorcineGelatin, FOOD.derivedFrom, FOOD.PorkSrc))
        graph.add((FOOD.PorkSrc, RDF.type, FOOD.Porcine))

        # Compliant Agar-Agar (PlantOrigin)
        graph.add((FOOD.AgarAgar, RDF.type, FOOD.Ingredient))
        graph.add((FOOD.AgarAgar, FOOD.hasFunctionalRole, FOOD.GellingAgent))
        graph.add((FOOD.AgarAgar, FOOD.derivedFrom, FOOD.SeaweedSrc))
        graph.add((FOOD.SeaweedSrc, RDF.type, FOOD.PlantOrigin))

        # Non-compliant Bovine Gelatin (AnimalOrigin)
        graph.add((FOOD.BovineGelatin, RDF.type, FOOD.Ingredient))
        graph.add((FOOD.BovineGelatin, FOOD.hasFunctionalRole, FOOD.GellingAgent))
        graph.add((FOOD.BovineGelatin, FOOD.derivedFrom, FOOD.CowSrc))
        graph.add((FOOD.CowSrc, RDF.type, FOOD.Bovine))

        # High ethanol extract with same role (should be excluded)
        graph.add((FOOD.AlcoholicGel, RDF.type, FOOD.Ingredient))
        graph.add((FOOD.AlcoholicGel, FOOD.hasFunctionalRole, FOOD.GellingAgent))
        graph.add((FOOD.AlcoholicGel, FOOD.derivedFrom, FOOD.SeaweedSrc))
        graph.add((FOOD.AlcoholicGel, FOOD.ethanolPercentage, Literal(1.2)))

        inferred = _run_rule(graph, "substitution_rules.sparql")
        subs = set(inferred.objects(FOOD.PorcineGelatin, FOOD.hasSuggestedSubstitute))
        self.assertEqual(subs, {FOOD.AgarAgar})


if __name__ == "__main__":
    unittest.main()
