import unittest
from pathlib import Path

from rdflib import Literal, RDF

from src.knowledge_engine import FOOD, KnowledgeEngine
from src.reformulation import candidates, simulate


ROOT = Path(__file__).resolve().parents[1]


class ReformulationTests(unittest.TestCase):
    def setUp(self):
        self.engine = KnowledgeEngine.from_turtle(
            ROOT / "ontology/sample_tbox.ttl", ROOT / "ontology/sample_abox.ttl"
        )

    def test_matches_are_provisional_and_exclude_known_failures(self):
        graph = self.engine.graph
        graph.add((FOOD.BadAlternative, RDF.type, FOOD.Ingredient))
        graph.add((FOOD.BadAlternative, FOOD.hasFunctionalRole, FOOD.SampleRole))
        graph.add((FOOD.BadAlternative, FOOD.ethanolPercentage, Literal(0.6)))
        matches = candidates(self.engine, FOOD.SampleAdditive, [FOOD.Halal, FOOD.Kosher])
        self.assertEqual([item[0] for item in matches], [FOOD.SampleAlternative])
        self.assertEqual(set(matches[0][1].values()), {"Not assessed"})
        with self.assertRaises(ValueError):
            candidates(self.engine, FOOD.SampleAdditive, [])

    def test_simulation_reevaluates_without_changing_original_graph(self):
        before = set(self.engine.graph)
        result = simulate(self.engine, FOOD.SampleBread, FOOD.SampleAdditive, FOOD.SampleAlternative)
        self.assertEqual(result[FOOD.Halal]["status"], "Not assessed")
        self.assertEqual(result[FOOD.Kosher]["status"], "Not assessed")
        self.assertEqual(set(self.engine.graph), before)
        self.assertEqual(self.engine.evaluate(FOOD.SampleBread)[FOOD.Halal]["status"], "Fail")

    def test_rejects_cycle_or_unrelated_ingredient(self):
        with self.assertRaises(ValueError):
            simulate(self.engine, FOOD.SampleBread, FOOD.SampleAdditive, FOOD.SampleDough)
        with self.assertRaises(ValueError):
            simulate(self.engine, FOOD.SampleBread, FOOD.SampleAlternative, FOOD.SampleFlour)
