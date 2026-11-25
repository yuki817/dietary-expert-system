import unittest

from rdflib import Graph, Literal, RDFS

from src.graph_visualizer import edge_label, graph_data, ingredient_path, label, node_level
from src.knowledge_engine import FOOD, KnowledgeEngine


class GraphVisualizerTests(unittest.TestCase):
    def test_graph_includes_direct_edges_sources_certificates_and_flags(self):
        graph = Graph()
        graph.add((FOOD.P, FOOD.containsIngredient, FOOD.A))
        graph.add((FOOD.A, FOOD.containsIngredient, FOOD.B))
        graph.add((FOOD.B, FOOD.derivedFrom, FOOD.Source))
        graph.add((FOOD.B, FOOD.hasCertificate, FOOD.Cert))
        engine = KnowledgeEngine(graph)
        nodes, edges = graph_data(engine, FOOD.P, {FOOD.B})
        self.assertEqual(ingredient_path(engine, FOOD.P, FOOD.B), [FOOD.P, FOOD.A, FOOD.B])
        self.assertEqual(ingredient_path(engine, FOOD.P, FOOD.Unrelated), [])
        self.assertEqual(nodes[FOOD.B], "flagged")
        self.assertEqual(nodes[FOOD.Source], "origin")
        self.assertEqual(nodes[FOOD.Cert], "certificate")
        self.assertIn((FOOD.A, FOOD.B, FOOD.containsIngredient), edges)
        self.assertIn((FOOD.B, FOOD.Source, FOOD.derivedFrom), edges)
        self.assertIn((FOOD.B, FOOD.Cert, FOOD.hasCertificate), edges)

    def test_labels_include_literals(self):
        graph = Graph()
        graph.add((FOOD.A, RDFS.label, Literal("Example")))
        self.assertEqual(label(graph, FOOD.A), "Example")
        self.assertEqual(label(graph, Literal("Text")), "Text")
        self.assertEqual(label(graph, FOOD.containsIngredient), "contains ingredient")
        self.assertEqual(edge_label(graph, FOOD.containsIngredient), "contains")
        self.assertEqual(edge_label(graph, FOOD.derivedFrom), "derived from")
        self.assertEqual(edge_label(graph, FOOD.hasCertificate), "certified by")

    def test_node_level_computes_hierarchy_depth(self):
        graph = Graph()
        graph.add((FOOD.P, FOOD.containsIngredient, FOOD.A))
        graph.add((FOOD.A, FOOD.containsIngredient, FOOD.B))
        graph.add((FOOD.B, FOOD.derivedFrom, FOOD.Source))
        engine = KnowledgeEngine(graph)
        nodes, edges = graph_data(engine, FOOD.P, {FOOD.B})
        levels = node_level(FOOD.P, nodes, edges)
        self.assertEqual(levels[FOOD.P], 0)
        self.assertEqual(levels[FOOD.A], 1)
        self.assertEqual(levels[FOOD.B], 2)
        self.assertEqual(levels[FOOD.Source], 3)
