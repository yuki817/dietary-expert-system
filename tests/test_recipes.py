import unittest

from rdflib import Graph, RDF

from src.knowledge_engine import FOOD, KnowledgeEngine
from src.recipes import RecipeBuilder


class RecipeTests(unittest.TestCase):
    def setUp(self):
        self.source = Graph()
        self.source.add((FOOD.CatalogIngredient, RDF.type, FOOD.Ingredient))

    def test_nested_recipe_is_isolated_and_evaluated(self):
        first = RecipeBuilder(self.source, "Recipe one")
        second = RecipeBuilder(self.source, "Recipe two")
        parent = first.add_ingredient(first.product, "Flavor")
        first.add_ingredient(parent, "Extract", 0.6)
        first.link_ingredient(parent, FOOD.CatalogIngredient)
        self.assertEqual(KnowledgeEngine(first.graph).evaluate(first.product)[FOOD.Halal]["status"], "Fail")
        self.assertEqual(KnowledgeEngine(second.graph).direct_ingredients(second.product), [])
        self.assertEqual(len(self.source), 1)
        self.assertNotIn((first.product, RDF.type, FOOD.FoodProduct), self.source)

    def test_rejects_cycles_invalid_parents_and_values(self):
        builder = RecipeBuilder(self.source, "Recipe")
        child = builder.add_ingredient(builder.product, "Child")
        for parent, ingredient in [(child, child), (FOOD.CatalogIngredient, child)]:
            with self.subTest(parent=parent), self.assertRaises(ValueError):
                builder.link_ingredient(parent, ingredient)
        with self.assertRaises(ValueError):
            builder.add_ingredient(child, "Bad", 101)
        with self.assertRaises(ValueError):
            builder.add_ingredient(child, " ")
        with self.assertRaises(ValueError):
            RecipeBuilder(self.source, " ")
