import unittest

from rdflib import Graph, Literal, OWL, RDF, RDFS, XSD

from src.graph_visualizer import abox_product_graph_data, edge_label, graph_data, ingredient_path, label, node_level, ontology_graph_data
from src.knowledge_engine import FOOD, KnowledgeEngine


class GraphVisualizerTests(unittest.TestCase):
    def test_abox_product_view_excludes_unrelated_products(self):
        graph = Graph()
        graph.add((FOOD.P, FOOD.containsIngredient, FOOD.A))
        graph.add((FOOD.A, FOOD.containsIngredient, FOOD.B))
        graph.add((FOOD.B, FOOD.derivedFrom, FOOD.Source))
        graph.add((FOOD.B, FOOD.hasCertificate, FOOD.Cert))
        graph.add((FOOD.B, FOOD.hasFunctionalRole, FOOD.Role))
        graph.add((FOOD.OtherProduct, FOOD.containsIngredient, FOOD.OtherIngredient))
        nodes, edges = abox_product_graph_data(KnowledgeEngine(graph), FOOD.P)
        self.assertEqual(set(nodes), {FOOD.P, FOOD.A, FOOD.B, FOOD.Source, FOOD.Cert, FOOD.Role})
        self.assertIn((FOOD.B, FOOD.hasFunctionalRole, FOOD.Role), edges)
        self.assertNotIn(FOOD.OtherProduct, nodes)

    def test_ontology_graph_can_include_literal_values(self):
        graph = Graph()
        graph.add((FOOD.A, FOOD.containsIngredient, FOOD.B))
        graph.add((FOOD.A, RDFS.label, Literal("Example")))
        graph.add((FOOD.OnlyLabel, RDFS.label, Literal("No relationships")))
        nodes, edges = ontology_graph_data(graph)
        self.assertEqual(set(nodes), {FOOD.A, FOOD.B})
        self.assertEqual(edges, [(FOOD.A, FOOD.containsIngredient, FOOD.B)])
        nodes, edges = ontology_graph_data(graph, include_literals=True)
        self.assertIn(Literal("Example"), nodes)
        self.assertIn((FOOD.A, RDFS.label, Literal("Example")), edges)

    def test_ontology_graph_omits_vocabulary_nodes_but_keeps_domain_types(self):
        graph = Graph()
        graph.add((FOOD.Ingredient, RDF.type, OWL.Class))
        graph.add((FOOD.A, RDF.type, FOOD.Ingredient))
        graph.add((FOOD.ethanolPercentage, RDFS.range, XSD.float))
        nodes, edges = ontology_graph_data(graph)
        self.assertEqual(set(nodes), {FOOD.A, FOOD.Ingredient})
        self.assertEqual(edges, [(FOOD.A, RDF.type, FOOD.Ingredient)])

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
