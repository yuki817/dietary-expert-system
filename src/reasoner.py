"""Member 2 RDFLib inference engine executing full SPARQL CONSTRUCT rule sets."""

from hashlib import sha256
from pathlib import Path

from rdflib import Graph, Literal, RDF, RDFS, URIRef

from src.knowledge_engine import FOOD, RULES, STANDARDS, KnowledgeEngine


COMPLETE_RULE_FILES = (
    "halal.sparql",
    "halal_audit.sparql",
    "kosher.sparql",
    "vegan_veg.sparql",
    "substitution_rules.sparql",
)

ONTOLOGY_DIR = Path(__file__).resolve().parent.parent / "ontology"


def _clone_graph(source: Graph) -> Graph:
    clone = Graph()
    for prefix, namespace in source.namespaces():
        clone.bind(prefix, namespace)
    for triple in source:
        clone.add(triple)
    return clone


class DietaryReasoner:
    """Deterministic SPARQL CONSTRUCT reasoner with Pass / Audit Required / Fail evaluation."""

    def __init__(self, graph: Graph, rule_files: tuple[str, ...] = COMPLETE_RULE_FILES):
        self.base_graph = graph
        self.rule_files = rule_files

    @classmethod
    def from_turtle(cls, *paths: str | Path) -> "DietaryReasoner":
        engine = KnowledgeEngine.from_turtle(*paths)
        return cls(engine.graph)

    @classmethod
    def from_default_files(cls) -> "DietaryReasoner":
        """Load ontology/tbox.ttl + abox.ttl if present, else fallback to sample/demo fixtures."""
        primary = (ONTOLOGY_DIR / "tbox.ttl", ONTOLOGY_DIR / "abox.ttl")
        alt = (ONTOLOGY_DIR / "food_compliance_tbox.ttl", ONTOLOGY_DIR / "food_compliance_abox.ttl")
        if all(p.exists() for p in primary):
            return cls.from_turtle(*primary)
        if all(p.exists() for p in alt):
            return cls.from_turtle(*alt)
        return cls.from_turtle(
            ONTOLOGY_DIR / "sample_tbox.ttl",
            ONTOLOGY_DIR / "sample_abox.ttl",
            ONTOLOGY_DIR / "demo_abox.ttl",
        )

    def products(self) -> list[URIRef]:
        return KnowledgeEngine(self.base_graph).products()

    def ingredients(self) -> list[URIRef]:
        return KnowledgeEngine(self.base_graph).ingredients()

    def _missing_origin_leaves(self, product: URIRef) -> list[URIRef]:
        """Return reachable leaf ingredients under product that lack a derivedFrom origin."""
        engine = KnowledgeEngine(self.base_graph)
        edges = engine.ingredient_edges(product)
        children = {child for _, child in edges}
        parents = {parent for parent, _ in edges}
        leaves = sorted(children - parents, key=str)
        missing = []
        for leaf in leaves:
            if not any(self.base_graph.objects(leaf, FOOD.derivedFrom)):
                missing.append(leaf)
        return missing

    def materialize(self) -> Graph:
        """Run all SPARQL CONSTRUCT rules and assert Pass / Audit / Fail triples on a graph copy."""
        enriched = _clone_graph(self.base_graph)
        for rule_name in self.rule_files:
            query_text = (RULES / rule_name).read_text(encoding="utf-8")
            result = self.base_graph.query(query_text)
            for triple in result.graph:
                enriched.add(triple)

        for product in self.products():
            edges = KnowledgeEngine(self.base_graph).ingredient_edges(product)
            missing_leaves = self._missing_origin_leaves(product)
            has_any_ingredients = bool(edges)

            if not has_any_ingredients:
                for standard in STANDARDS:
                    digest = sha256(f"{product}|empty|{standard}".encode("utf-8")).hexdigest()
                    issue = URIRef(f"http://example.org/issue/{digest}")
                    enriched.add((product, FOOD.requiresAuditFor, standard))
                    enriched.add((product, FOOD.hasIssue, issue))
                    enriched.add((issue, RDF.type, FOOD.ComplianceIssue))
                    enriched.add((issue, FOOD.standard, standard))
                    enriched.add((issue, RDFS.label, Literal("Audit required: product has no declared ingredients.")))
            elif missing_leaves:
                for leaf in missing_leaves:
                    for standard in STANDARDS:
                        digest = sha256(f"{product}|missing-origin|{standard}|{leaf}".encode("utf-8")).hexdigest()
                        issue = URIRef(f"http://example.org/issue/{digest}")
                        enriched.add((product, FOOD.requiresAuditFor, standard))
                        enriched.add((product, FOOD.hasIssue, issue))
                        enriched.add((issue, RDF.type, FOOD.ComplianceIssue))
                        enriched.add((issue, FOOD.standard, standard))
                        enriched.add((issue, FOOD.flaggedIngredient, leaf))
                        enriched.add(
                            (issue, RDFS.label, Literal(f"Audit required: missing biological origin for {leaf}."))
                        )

            for standard in STANDARDS:
                failed = (product, FOOD.isNonCompliantWith, standard) in enriched
                audit = (product, FOOD.requiresAuditFor, standard) in enriched
                if not failed and not audit:
                    enriched.add((product, FOOD.isCompliantWith, standard))

        return enriched

    def evaluate_product(self, product: URIRef) -> dict:
        """Evaluate a product across all dietary standards, returning Pass, Audit Required, or Fail."""
        if (product, RDF.type, FOOD.FoodProduct) not in self.base_graph:
            raise ValueError(f"Not an explicitly typed food product: {product}")

        enriched = self.materialize()
        results = {}
        for standard in STANDARDS:
            if (product, FOOD.isNonCompliantWith, standard) in enriched:
                status = "Fail"
            elif (product, FOOD.requiresAuditFor, standard) in enriched:
                status = "Audit Required"
            elif (product, FOOD.isCompliantWith, standard) in enriched:
                status = "Pass"
            else:
                status = "Not assessed"

            issues = []
            for issue in sorted(enriched.objects(product, FOOD.hasIssue), key=str):
                if (issue, FOOD.standard, standard) not in enriched:
                    continue
                issues.append({
                    "id": issue,
                    "message": str(enriched.value(issue, RDFS.label)),
                    "ingredients": sorted(enriched.objects(issue, FOOD.flaggedIngredient), key=str),
                })
            results[standard] = {"status": status, "issues": issues}
        return results
