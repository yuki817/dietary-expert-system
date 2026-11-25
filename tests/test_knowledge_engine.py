import tempfile
import unittest
from pathlib import Path

from rdflib import Graph

from src.knowledge_engine import FOOD, KnowledgeEngine, KnowledgeGraphError


ROOT = Path(__file__).resolve().parents[1]


class KnowledgeEngineTests(unittest.TestCase):
    def test_loads_sample_and_returns_nested_direct_edges(self):
        engine = KnowledgeEngine.from_turtle(
            ROOT / "ontology/sample_tbox.ttl", ROOT / "ontology/sample_abox.ttl"
        )
        self.assertEqual(engine.products(), [FOOD.SampleBread])
        self.assertEqual(engine.ingredients(), [FOOD.SampleDough, FOOD.SampleFlour])
        self.assertEqual(engine.direct_ingredients(FOOD.SampleBread), [FOOD.SampleDough])
        self.assertEqual(
            engine.ingredient_edges(FOOD.SampleBread),
            [(FOOD.SampleBread, FOOD.SampleDough), (FOOD.SampleDough, FOOD.SampleFlour)],
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


if __name__ == "__main__":
    unittest.main()
