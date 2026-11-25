import tempfile
import unittest
from pathlib import Path

from rdflib import Graph, Literal, RDF, RDFS

from src.knowledge_engine import FOOD, KnowledgeEngine, KnowledgeGraphError


ROOT = Path(__file__).resolve().parents[1]


class KnowledgeEngineTests(unittest.TestCase):
    def test_loads_sample_and_returns_nested_direct_edges(self):
        engine = KnowledgeEngine.from_turtle(
            ROOT / "ontology/sample_tbox.ttl", ROOT / "ontology/sample_abox.ttl"
        )
        self.assertEqual(engine.products(), [FOOD.SampleBread])
        self.assertEqual(engine.ingredients(), [FOOD.SampleAdditive, FOOD.SampleAlternative,
                                                FOOD.SampleDough, FOOD.SampleFlour])
        self.assertEqual(engine.direct_ingredients(FOOD.SampleBread), [FOOD.SampleDough])
        self.assertEqual(
            engine.ingredient_edges(FOOD.SampleBread),
            [(FOOD.SampleBread, FOOD.SampleDough), (FOOD.SampleDough, FOOD.SampleAdditive),
             (FOOD.SampleDough, FOOD.SampleFlour)],
        )

    def test_traversal_retains_shared_edges_and_terminates_on_cycles(self):
        graph = Graph()
        for parent, child in [(FOOD.P, FOOD.A), (FOOD.P, FOOD.B),
                              (FOOD.A, FOOD.C), (FOOD.B, FOOD.C), (FOOD.C, FOOD.A)]:
            graph.add((parent, FOOD.containsIngredient, child))
        self.assertEqual(len(KnowledgeEngine(graph).ingredient_edges(FOOD.P)), 5)

    def test_invalid_or_missing_files_report_the_path(self):
        with tempfile.TemporaryDirectory() as directory:
            invalid = Path(directory) / "invalid.ttl"
            invalid.write_text("this is not Turtle", encoding="utf-8")
            for path in (invalid, Path(directory) / "missing.ttl"):
                with self.subTest(path=path), self.assertRaises(KnowledgeGraphError) as error:
                    KnowledgeEngine.from_turtle(path)
                self.assertIn(str(path), str(error.exception))

    def test_requires_a_file(self):
        with self.assertRaises(KnowledgeGraphError):
            KnowledgeEngine.from_turtle()

    def test_provisional_rules_trace_nested_sources_and_are_repeatable(self):
        graph = Graph()
        graph.add((FOOD.P, RDF.type, FOOD.FoodProduct))
        graph.add((FOOD.P, FOOD.containsIngredient, FOOD.A))
        graph.add((FOOD.A, FOOD.containsIngredient, FOOD.B))
        graph.add((FOOD.B, FOOD.containsIngredient, FOOD.C))
        graph.add((FOOD.C, FOOD.derivedFrom, FOOD.Source))
        graph.add((FOOD.Source, RDF.type, FOOD.CustomPorcine))
        graph.add((FOOD.CustomPorcine, RDFS.subClassOf, FOOD.Porcine))
        engine = KnowledgeEngine(graph)
        before = set(graph)
        first = engine.evaluate(FOOD.P)
        self.assertEqual(first, engine.evaluate(FOOD.P))
        self.assertEqual(set(graph), before)
        self.assertEqual(first[FOOD.Halal]["status"], "Fail")
        self.assertEqual(first[FOOD.Kosher]["status"], "Fail")
        self.assertEqual(first[FOOD.Halal]["issues"][0]["ingredients"], [FOOD.C])
        self.assertEqual(first[FOOD.Vegan]["status"], "Not assessed")

    def test_ethanol_boundary_and_fail_over_audit(self):
        graph = Graph()
        for triple in [(FOOD.P, RDF.type, FOOD.FoodProduct),
                       (FOOD.P, FOOD.containsIngredient, FOOD.A),
                       (FOOD.A, FOOD.derivedFrom, FOOD.Source),
                       (FOOD.Source, RDF.type, FOOD.Bovine),
                       (FOOD.A, FOOD.ethanolPercentage, Literal(0.5))]:
            graph.add(triple)
        engine = KnowledgeEngine(graph)
        self.assertEqual(engine.evaluate(FOOD.P)[FOOD.Halal]["status"], "Audit Required")
        graph.set((FOOD.A, FOOD.ethanolPercentage, Literal(0.51)))
        halal = engine.evaluate(FOOD.P)[FOOD.Halal]
        self.assertEqual(halal["status"], "Fail")
        self.assertEqual(len(halal["issues"]), 2)
        graph.add((FOOD.A, FOOD.hasCertificate, FOOD.Cert))
        graph.add((FOOD.Cert, RDF.type, FOOD.HalalCert))
        self.assertEqual(len(engine.evaluate(FOOD.P)[FOOD.Halal]["issues"]), 1)

    def test_meat_dairy_and_vegetarian_rules(self):
        graph = Graph()
        graph.add((FOOD.P, RDF.type, FOOD.FoodProduct))
        for ingredient, source, kind in [(FOOD.Meat, FOOD.MSource, FOOD.MeatTissue),
                                         (FOOD.Milk, FOOD.DSource, FOOD.Dairy)]:
            graph.add((FOOD.P, FOOD.containsIngredient, ingredient))
            graph.add((ingredient, FOOD.derivedFrom, source))
            graph.add((source, RDF.type, kind))
        result = KnowledgeEngine(graph).evaluate(FOOD.P)
        self.assertEqual(result[FOOD.Kosher]["status"], "Fail")
        self.assertEqual(result[FOOD.Kosher]["issues"][0]["ingredients"], [FOOD.Meat, FOOD.Milk])
        self.assertEqual(result[FOOD.Vegetarian]["status"], "Fail")
        self.assertEqual(result[FOOD.Vegan]["status"], "Fail")


if __name__ == "__main__":
    unittest.main()
