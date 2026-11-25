"""Create isolated, session-local recipe and product/ingredient graphs."""

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
    def __init__(self, source: Graph, name: str | None = None):
        self.graph = Graph()
        for prefix, namespace in source.namespaces():
            self.graph.bind(prefix, namespace)
        for triple in source:
            self.graph.add(triple)
        self.owned: set[URIRef] = set()
        self.product: URIRef | None = None
        if name is not None:
            self.add_product(name)

    def _check_parent(self, parent):
        if parent not in self.owned and (parent, RDF.type, FOOD.FoodProduct) not in self.graph:
            raise ValueError("Choose the recipe or one of its custom ingredients as the parent.")

    def add_product(self, name: str, ingredients=(), comment: str | None = None) -> URIRef:
        name = _name(name)
        product = URIRef(f"urn:recipe:{uuid4()}")
        self.graph.add((product, RDF.type, FOOD.FoodProduct))
        self.graph.add((product, RDFS.label, Literal(name)))
        if comment and comment.strip():
            self.graph.add((product, RDFS.comment, Literal(comment.strip())))
        self.owned.add(product)
        self.product = product
        for ingredient in ingredients or ():
            self.link_ingredient(product, ingredient)
        return product

    def add_ingredient(
        self,
        parent,
        name: str,
        ethanol=None,
        origin=None,
        role=None,
        certificates=(),
        *,
        origins=(),
        e_number: str | None = None,
        comment: str | None = None,
        sub_ingredients=(),
    ) -> URIRef:
        if parent is not None:
            self._check_parent(parent)
        name = _name(name)
        if ethanol is not None and (not math.isfinite(ethanol) or not 0 <= ethanol <= 100):
            raise ValueError("Ethanol percentage must be between 0 and 100.")
        ingredient = URIRef(f"urn:recipe:{uuid4()}")
        self.graph.add((ingredient, RDF.type, FOOD.Ingredient))
        self.graph.add((ingredient, RDFS.label, Literal(name)))
        if e_number and e_number.strip():
            self.graph.add((ingredient, FOOD.eNumber, Literal(e_number.strip())))
        if comment and comment.strip():
            self.graph.add((ingredient, RDFS.comment, Literal(comment.strip())))
        if ethanol is not None:
            self.graph.add((ingredient, FOOD.ethanolPercentage, Literal(ethanol)))

        all_origins = []
        if origin is not None:
            all_origins.append(origin)
        for item in origins or ():
            if item is not None and item not in all_origins:
                all_origins.append(item)
        for item in all_origins:
            self.graph.add((ingredient, FOOD.derivedFrom, item))

        if role is not None:
            self.graph.add((ingredient, FOOD.hasFunctionalRole, role))
        for cert in certificates or ():
            self.graph.add((ingredient, FOOD.hasCertificate, cert))

        self.owned.add(ingredient)
        for sub in sub_ingredients or ():
            self.link_ingredient(ingredient, sub)
        if parent is not None:
            self.graph.add((parent, FOOD.containsIngredient, ingredient))
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
