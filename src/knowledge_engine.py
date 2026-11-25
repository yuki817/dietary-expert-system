"""Load and inspect the project's RDF knowledge graph."""

from pathlib import Path

from rdflib import Graph, Namespace, RDF, URIRef
from rdflib.exceptions import ParserError


FOOD = Namespace("http://example.org/food-compliance#")


class KnowledgeGraphError(ValueError):
    """A knowledge graph input could not be loaded."""


class KnowledgeEngine:
    def __init__(self, graph: Graph):
        self.graph = graph

    @classmethod
    def from_turtle(cls, *paths: str | Path) -> "KnowledgeEngine":
        """Load Turtle files into a new graph, without modifying source files."""
        if not paths:
            raise KnowledgeGraphError("Provide at least one Turtle file.")
        graph = Graph()
        graph.bind("food", FOOD)
        for path in paths:
            try:
                graph.parse(str(path), format="turtle")
            except (OSError, ParserError, SyntaxError, UnicodeError) as exc:
                raise KnowledgeGraphError(f"Could not load Turtle file {path}: {exc}") from exc
        return cls(graph)

    def products(self) -> list[URIRef]:
        """Return explicitly typed products, ordered by IRI."""
        return sorted(self.graph.subjects(RDF.type, FOOD.FoodProduct), key=str)

    def ingredients(self) -> list[URIRef]:
        """Return explicitly typed ingredients, ordered by IRI."""
        return sorted(self.graph.subjects(RDF.type, FOOD.Ingredient), key=str)

    def direct_ingredients(self, node: URIRef) -> list[URIRef]:
        """Return ingredients linked directly to a product or ingredient."""
        return sorted(set(self.graph.objects(node, FOOD.containsIngredient)), key=str)

    def ingredient_edges(self, root: URIRef) -> list[tuple[URIRef, URIRef]]:
        """Return reachable direct edges, retaining shared nodes and handling cycles."""
        edges = set()
        visited = set()
        pending = [root]
        while pending:
            parent = pending.pop()
            if parent in visited:
                continue
            visited.add(parent)
            for child in self.direct_ingredients(parent):
                edges.add((parent, child))
                if child not in visited:
                    pending.append(child)
        return sorted(edges, key=lambda edge: (str(edge[0]), str(edge[1])))
