import unittest

from rdflib import Graph, Literal, RDF, RDFS

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

    def test_add_ingredient_supports_origin_role_and_certificates(self):
        self.source.add((FOOD.Src_Plant, RDF.type, FOOD.PlantOrigin))
        self.source.add((FOOD.GellingAgent, RDF.type, FOOD.FunctionalRole))
        self.source.add((FOOD.HalalCert_01, RDF.type, FOOD.HalalCert))
        builder = RecipeBuilder(self.source, "Certified Plant Jelly")
        ing = builder.add_ingredient(
            builder.product,
            "Custom Agar",
            ethanol=0.0,
            origin=FOOD.Src_Plant,
            role=FOOD.GellingAgent,
            certificates=[FOOD.HalalCert_01],
        )
        self.assertIn((ing, FOOD.derivedFrom, FOOD.Src_Plant), builder.graph)
        self.assertIn((ing, FOOD.hasFunctionalRole, FOOD.GellingAgent), builder.graph)
        self.assertIn((ing, FOOD.hasCertificate, FOOD.HalalCert_01), builder.graph)

    def test_add_product_and_standalone_labelled_ingredient(self):
        self.source.add((FOOD.Src_Plant, RDF.type, FOOD.PlantOrigin))
        self.source.add((FOOD.Byprod_Dairy, RDF.type, FOOD.Dairy))
        self.source.add((FOOD.Emulsifier, RDF.type, FOOD.FunctionalRole))
        self.source.add((FOOD.HalalCert_01, RDF.type, FOOD.HalalCert))

        builder = RecipeBuilder(self.source)
        ing = builder.add_ingredient(
            None,
            "Custom Lecithin Mix",
            ethanol=0.0,
            origins=[FOOD.Src_Plant, FOOD.Byprod_Dairy],
            role=FOOD.Emulsifier,
            certificates=[FOOD.HalalCert_01],
            e_number="E322b",
            comment="Custom compound emulsifier",
            sub_ingredients=[FOOD.CatalogIngredient],
        )
        self.assertIn((ing, RDF.type, FOOD.Ingredient), builder.graph)
        self.assertIn((ing, RDFS.label, Literal("Custom Lecithin Mix")), builder.graph)
        self.assertIn((ing, FOOD.eNumber, Literal("E322b")), builder.graph)
        self.assertIn((ing, RDFS.comment, Literal("Custom compound emulsifier")), builder.graph)
        self.assertIn((ing, FOOD.derivedFrom, FOOD.Src_Plant), builder.graph)
        self.assertIn((ing, FOOD.derivedFrom, FOOD.Byprod_Dairy), builder.graph)
        self.assertIn((ing, FOOD.containsIngredient, FOOD.CatalogIngredient), builder.graph)

        product = builder.add_product(
            "Artisan Chocolate Bar",
            ingredients=[ing],
            comment="Dark chocolate bar with custom emulsifier",
        )
        self.assertIn((product, RDF.type, FOOD.FoodProduct), builder.graph)
        self.assertIn((product, RDFS.label, Literal("Artisan Chocolate Bar")), builder.graph)
        self.assertIn((product, RDFS.comment, Literal("Dark chocolate bar with custom emulsifier")), builder.graph)
        self.assertIn((product, FOOD.containsIngredient, ing), builder.graph)
