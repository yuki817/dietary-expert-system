"""Member 2 SPARQL SELECT query functions for the 3 core use-cases."""

from typing import Iterable
from uuid import uuid4

from rdflib import Graph, RDF, URIRef

from src.knowledge_engine import FOOD, STANDARDS, KnowledgeEngine
from src.reasoner import DietaryReasoner, _clone_graph


SCORECARD_STATUS_QUERY = """
PREFIX food: <http://example.org/food-compliance#>

SELECT ?standard ?relation
WHERE {
  VALUES ?relation { food:isNonCompliantWith food:requiresAuditFor food:isCompliantWith }
  ?product ?relation ?standard .
}
"""

SCORECARD_ISSUES_QUERY = """
PREFIX food: <http://example.org/food-compliance#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?issue ?standard ?message ?ingredient
WHERE {
  ?product food:hasIssue ?issue .
  ?issue (food:forStandard|food:standard) ?standard ;
         rdfs:label ?message .
  OPTIONAL { ?issue food:flaggedIngredient ?ingredient . }
}
ORDER BY ?issue ?ingredient
"""

TRACE_EDGES_QUERY = """
PREFIX food: <http://example.org/food-compliance#>

SELECT DISTINCT ?parent ?child
WHERE {
  ?product food:containsIngredient* ?parent .
  ?parent food:containsIngredient ?child .
}
ORDER BY ?parent ?child
"""

TRACE_INGREDIENTS_QUERY = """
PREFIX food: <http://example.org/food-compliance#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?ingredient ?label ?ethanol ?role
WHERE {
  ?product food:containsIngredient+ ?ingredient .
  OPTIONAL { ?ingredient rdfs:label ?label . }
  OPTIONAL { ?ingredient food:ethanolPercentage ?ethanol . }
  OPTIONAL { ?ingredient food:hasFunctionalRole ?role . }
}
ORDER BY ?ingredient
"""

TRACE_ORIGINS_QUERY = """
PREFIX food: <http://example.org/food-compliance#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT DISTINCT ?ingredient ?origin ?originType
WHERE {
  ?product food:containsIngredient+ ?ingredient .
  ?ingredient food:derivedFrom ?origin .
  ?origin rdf:type ?originType .
}
ORDER BY ?ingredient ?origin ?originType
"""

TRACE_CERTIFICATES_QUERY = """
PREFIX food: <http://example.org/food-compliance#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT DISTINCT ?ingredient ?certificate ?certificateType
WHERE {
  ?product food:containsIngredient+ ?ingredient .
  ?ingredient food:hasCertificate ?certificate .
  ?certificate rdf:type ?certificateType .
}
ORDER BY ?ingredient ?certificate ?certificateType
"""

SUBSTITUTES_QUERY = """
PREFIX food: <http://example.org/food-compliance#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT DISTINCT ?substitute ?role ?source ?sourceType
WHERE {
  ?ingredient food:hasSuggestedSubstitute ?substitute ;
              food:hasFunctionalRole ?role .
  ?substitute food:hasFunctionalRole ?role ;
              food:derivedFrom ?source .
  ?source rdf:type ?sourceType .
}
ORDER BY ?substitute
"""


def query_compliance_scorecard(enriched_graph: Graph, product: URIRef) -> dict:
    """Use-Case 1: SPARQL SELECT query extracting compliance statuses and issues per standard."""
    relations_by_std: dict[URIRef, set[URIRef]] = {std: set() for std in STANDARDS}
    for row in enriched_graph.query(SCORECARD_STATUS_QUERY, initBindings={"product": product}):
        if row.standard in relations_by_std:
            relations_by_std[row.standard].add(row.relation)

    issues_by_std: dict[URIRef, dict[URIRef, dict]] = {std: {} for std in STANDARDS}
    for row in enriched_graph.query(SCORECARD_ISSUES_QUERY, initBindings={"product": product}):
        if row.standard not in issues_by_std:
            continue
        bucket = issues_by_std[row.standard].setdefault(
            row.issue,
            {"id": row.issue, "message": str(row.message), "ingredients": []},
        )
        if row.ingredient is not None and row.ingredient not in bucket["ingredients"]:
            bucket["ingredients"].append(row.ingredient)

    scorecard = {}
    for std in STANDARDS:
        rels = relations_by_std[std]
        if FOOD.isNonCompliantWith in rels:
            status = "Fail"
        elif FOOD.requiresAuditFor in rels:
            status = "Audit Required"
        elif FOOD.isCompliantWith in rels:
            status = "Pass"
        else:
            status = "Not assessed"
        scorecard[std] = {
            "status": status,
            "issues": list(issues_by_std[std].values()),
        }
    return scorecard


def query_supply_chain_trace(graph: Graph, product: URIRef) -> dict:
    """Use-Case 2: Recursive SPARQL property path queries extracting the full BOM tree."""
    bindings = {"product": product}
    edges = [
        {"parent": row.parent, "child": row.child}
        for row in graph.query(TRACE_EDGES_QUERY, initBindings=bindings)
    ]
    ingredients = [
        {
            "ingredient": row.ingredient,
            "label": str(row.label) if row.label is not None else None,
            "ethanol": float(row.ethanol) if row.ethanol is not None else None,
            "role": row.role,
        }
        for row in graph.query(TRACE_INGREDIENTS_QUERY, initBindings=bindings)
    ]
    origins = [
        {
            "ingredient": row.ingredient,
            "origin": row.origin,
            "origin_type": row.originType,
        }
        for row in graph.query(TRACE_ORIGINS_QUERY, initBindings=bindings)
    ]
    certificates = [
        {
            "ingredient": row.ingredient,
            "certificate": row.certificate,
            "certificate_type": row.certificateType,
        }
        for row in graph.query(TRACE_CERTIFICATES_QUERY, initBindings=bindings)
    ]
    return {
        "product": product,
        "edges": edges,
        "ingredients": ingredients,
        "origins": origins,
        "certificates": certificates,
    }


def query_substitutes(
    enriched_graph: Graph,
    flagged_ingredient: URIRef,
    target_standards: Iterable[URIRef] = STANDARDS,
) -> list[dict]:
    """Use-Case 3: SPARQL SELECT querying inferred food:hasSuggestedSubstitute candidates."""
    targets = tuple(target_standards)
    if not targets or any(t not in STANDARDS for t in targets):
        raise ValueError("Choose at least one supported target standard.")

    rows = list(
        enriched_graph.query(
            SUBSTITUTES_QUERY,
            initBindings={"ingredient": flagged_ingredient},
        )
    )
    results = []
    seen = set()
    for row in rows:
        sub = row.substitute
        if sub in seen:
            continue
        seen.add(sub)
        probe_graph = _clone_graph(enriched_graph)
        probe_product = URIRef(f"urn:substitute-probe:{uuid4()}")
        probe_graph.add((probe_product, RDF.type, FOOD.FoodProduct))
        probe_graph.add((probe_product, FOOD.containsIngredient, sub))
        probe_eval = DietaryReasoner(probe_graph).evaluate_product(probe_product)
        statuses = {target: probe_eval[target]["status"] for target in targets}
        if all(status == "Pass" for status in statuses.values()):
            results.append({
                "substitute": sub,
                "role": row.role,
                "source": row.source,
                "source_type": row.sourceType,
                "statuses": statuses,
            })
    return results


def simulate_reformulation(
    reasoner: DietaryReasoner,
    product: URIRef,
    original_ingredient: URIRef,
    replacement_ingredient: URIRef,
) -> dict:
    """Use-Case 3 Simulation: Replace every occurrence of original_ingredient in product and re-run inference."""
    if original_ingredient == replacement_ingredient:
        raise ValueError("Select a different replacement ingredient.")
    if (replacement_ingredient, RDF.type, FOOD.Ingredient) not in reasoner.base_graph:
        raise ValueError("Replacement must be an explicitly typed Ingredient in the graph.")

    engine = KnowledgeEngine(reasoner.base_graph)
    parents = {parent for parent, child in engine.ingredient_edges(product) if child == original_ingredient}
    if not parents:
        raise ValueError("The original ingredient is not part of this product.")
    descendants = {child for _, child in engine.ingredient_edges(replacement_ingredient)} | {replacement_ingredient}
    if parents & descendants:
        raise ValueError("This replacement would create a cycle.")

    modified_graph = _clone_graph(reasoner.base_graph)
    for parent in parents:
        modified_graph.remove((parent, FOOD.containsIngredient, original_ingredient))
        modified_graph.add((parent, FOOD.containsIngredient, replacement_ingredient))

    return DietaryReasoner(modified_graph, rule_files=reasoner.rule_files).evaluate_product(product)
