"""Load and inspect the project's RDF knowledge graph."""

from pathlib import Path

from rdflib import Graph, Namespace, RDF, RDFS, URIRef
from rdflib.exceptions import ParserError


FOOD = Namespace("http://example.org/food-compliance#")
RULES = Path(__file__).resolve().parent.parent / "rules"
RULE_FILES = ("halal.sparql", "halal_audit.sparql", "kosher_porcine.sparql",
              "kosher_meat_dairy.sparql", "vegetarian_vegan.sparql")
STANDARDS = (FOOD.Halal, FOOD.Kosher, FOOD.Vegetarian, FOOD.Vegan)


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

    def evaluate(self, product: URIRef) -> dict:
        """Evaluate implemented rules; absence of findings is not yet a pass."""
        if (product, RDF.type, FOOD.FoodProduct) not in self.graph:
            raise ValueError(f"Not an explicitly typed food product: {product}")

        inferred = Graph()
        for name in RULE_FILES:
            path = RULES / name
            result = self.graph.query(path.read_text(encoding="utf-8"))
            for triple in result.graph:
                inferred.add(triple)

        results = {}
        for standard in STANDARDS:
            if (product, FOOD.isNonCompliantWith, standard) in inferred:
                status = "Fail"
            elif (product, FOOD.requiresAuditFor, standard) in inferred:
                status = "Audit Required"
            else:
                status = "Not assessed"
            issues = []
            for issue in sorted(inferred.objects(product, FOOD.hasIssue), key=str):
                if (issue, FOOD.forStandard, standard) not in inferred:
                    continue
                issues.append({
                    "id": issue,
                    "message": str(inferred.value(issue, RDFS.label)),
                    "ingredients": sorted(inferred.objects(issue, FOOD.flaggedIngredient), key=str),
                })
            results[standard] = {"status": status, "issues": issues}
        return results
