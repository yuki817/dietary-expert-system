import unittest

from src.knowledge_engine import FOOD, STANDARDS
from src.queries import (
    query_compliance_scorecard,
    query_substitutes,
    query_supply_chain_trace,
    simulate_multi_reformulation,
    simulate_reformulation,
)
from src.reasoner import DietaryReasoner
from tests.test_reasoner import _build_benchmark_graph


class QueriesTests(unittest.TestCase):
    def setUp(self):
        self.base_graph = _build_benchmark_graph()
        self.reasoner = DietaryReasoner(self.base_graph)
        self.enriched = self.reasoner.materialize()

    def test_query_compliance_scorecard_uses_sparql_select_for_status_and_issues(self):
        candy_score = query_compliance_scorecard(self.enriched, FOOD.StrawberryGummyCandy)
        for std in STANDARDS:
            self.assertEqual(candy_score[std]["status"], "Fail")
            self.assertGreaterEqual(len(candy_score[std]["issues"]), 1)

        ramen_score = query_compliance_scorecard(self.enriched, FOOD.PlantBasedRamen)
        for std in STANDARDS:
            self.assertEqual(ramen_score[std]["status"], "Pass")
            self.assertEqual(ramen_score[std]["issues"], [])

    def test_query_supply_chain_trace_extracts_nested_bom_origins_and_certificates(self):
        bread_trace = query_supply_chain_trace(self.enriched, FOOD.ArtisanDoughBread)
        ingredient_uris = {row["ingredient"] for row in bread_trace["ingredients"]}
        self.assertIn(FOOD.DoughConditioner, ingredient_uris)
        self.assertIn(FOOD.LCysteinePorcine, ingredient_uris)
        edges = {(row["parent"], row["child"]) for row in bread_trace["edges"]}
        self.assertIn((FOOD.ArtisanDoughBread, FOOD.DoughConditioner), edges)
        self.assertIn((FOOD.DoughConditioner, FOOD.LCysteinePorcine), edges)
        origins = {(row["ingredient"], row["origin"], row["origin_type"]) for row in bread_trace["origins"]}
        self.assertIn((FOOD.LCysteinePorcine, FOOD.PorcineSrc, FOOD.Porcine), origins)

        ramen_trace = query_supply_chain_trace(self.enriched, FOOD.PlantBasedRamen)
        certs = {(row["ingredient"], row["certificate"], row["certificate_type"]) for row in ramen_trace["certificates"]}
        self.assertIn((FOOD.AgarAgar, FOOD.HalalCert01, FOOD.HalalCert), certs)
        self.assertIn((FOOD.AgarAgar, FOOD.KosherCert01, FOOD.KosherCert), certs)

    def test_query_substitutes_and_simulate_reformulation_convert_product_to_pass(self):
        subs = query_substitutes(
            self.enriched,
            FOOD.LCysteinePorcine,
            target_standards=(FOOD.Halal, FOOD.Kosher, FOOD.Vegetarian, FOOD.Vegan),
        )
        sub_uris = [item["substitute"] for item in subs]
        self.assertEqual(sub_uris, [FOOD.MicrobialTG])
        self.assertEqual(subs[0]["role"], FOOD.DoughConditionerRole)

        simulated = simulate_reformulation(
            self.reasoner,
            FOOD.ArtisanDoughBread,
            FOOD.LCysteinePorcine,
            FOOD.MicrobialTG,
        )
        for std in STANDARDS:
            self.assertEqual(simulated[std]["status"], "Pass")

        # Vanilla Pastry reformulation: VanillaExtract -> SyntheticVanilla makes Halal Pass
        pastry_sim = simulate_reformulation(
            self.reasoner,
            FOOD.VanillaPastry,
            FOOD.VanillaExtract,
            FOOD.SyntheticVanilla,
        )
        self.assertEqual(pastry_sim[FOOD.Halal]["status"], "Pass")
        self.assertEqual(pastry_sim[FOOD.Kosher]["status"], "Pass")
        self.assertEqual(pastry_sim[FOOD.Vegetarian]["status"], "Pass")
        self.assertEqual(pastry_sim[FOOD.Vegan]["status"], "Fail")

    def test_simulate_multi_reformulation_replaces_multiple_flagged_ingredients_at_once(self):
        # StrawberryGummyCandy has PorcineGelatin AND Carmine; add BeetrootRed for Coloring
        from rdflib import Literal, RDF, RDFS
        self.base_graph.add((FOOD.BeetrootRed, RDF.type, FOOD.Ingredient))
        self.base_graph.add((FOOD.BeetrootRed, RDFS.label, Literal("Beetroot Red")))
        self.base_graph.add((FOOD.BeetrootRed, FOOD.derivedFrom, FOOD.PlantSrc))
        self.base_graph.add((FOOD.BeetrootRed, FOOD.hasFunctionalRole, FOOD.Coloring))

        simulated = simulate_multi_reformulation(
            self.reasoner,
            FOOD.StrawberryGummyCandy,
            {
                FOOD.PorcineGelatin: FOOD.AgarAgar,
                FOOD.Carmine: FOOD.BeetrootRed,
            },
        )
        for std in STANDARDS:
            self.assertEqual(simulated[std]["status"], "Pass")


if __name__ == "__main__":
    unittest.main()
