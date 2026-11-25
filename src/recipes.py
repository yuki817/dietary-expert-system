"""Create isolated, session-local recipe graphs."""

import math
from uuid import uuid4

from rdflib import Graph, Literal, RDF, RDFS, URIRef

from src.knowledge_engine import FOOD, KnowledgeEngine


def _name(value):
    value = value.strip()
    if not value:
        raise ValueError("Enter a name.")
    return value


class RecipeBuilder:
    def __init__(self, source: Graph, name: str):
        name = _name(name)
        self.graph = Graph()
        for prefix, namespace in source.namespaces():
            self.graph.bind(prefix, namespace)
        for triple in source:
            self.graph.add(triple)
        self.product = URIRef(f"urn:recipe:{uuid4()}")
        self.graph.add((self.product, RDF.type, FOOD.FoodProduct))
        self.graph.add((self.product, RDFS.label, Literal(name)))
        self.owned = {self.product}

    def _check_parent(self, parent):
        if parent not in self.owned:
            raise ValueError("Choose the recipe or one of its custom ingredients as the parent.")

    def add_ingredient(self, parent, name, ethanol=None, origin=None, role=None, certificates=()):
        self._check_parent(parent)
        name = _name(name)
        if ethanol is not None and (not math.isfinite(ethanol) or not 0 <= ethanol <= 100):
            raise ValueError("Ethanol percentage must be between 0 and 100.")
        ingredient = URIRef(f"urn:recipe:{uuid4()}")
        self.graph.add((ingredient, RDF.type, FOOD.Ingredient))
        self.graph.add((ingredient, RDFS.label, Literal(name)))
        if ethanol is not None:
            self.graph.add((ingredient, FOOD.ethanolPercentage, Literal(ethanol)))
        if origin is not None:
            self.graph.add((ingredient, FOOD.derivedFrom, origin))
        if role is not None:
            self.graph.add((ingredient, FOOD.hasFunctionalRole, role))
        for cert in certificates or ():
            self.graph.add((ingredient, FOOD.hasCertificate, cert))
        self.graph.add((parent, FOOD.containsIngredient, ingredient))
        self.owned.add(ingredient)
        return ingredient

    def link_ingredient(self, parent, ingredient):
        self._check_parent(parent)
        if (ingredient, RDF.type, FOOD.Ingredient) not in self.graph:
            raise ValueError("Choose an ingredient from the graph.")
        if ingredient == parent or any(
            child == parent for _, child in KnowledgeEngine(self.graph).ingredient_edges(ingredient)
        ):
            raise ValueError("This link would create a cycle.")
        self.graph.add((parent, FOOD.containsIngredient, ingredient))
