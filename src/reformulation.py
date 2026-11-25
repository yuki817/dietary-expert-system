"""Find provisional role matches and simulate substitutions in graph copies."""

from uuid import uuid4

from rdflib import Graph, RDF, URIRef

from src.knowledge_engine import FOOD, KnowledgeEngine, STANDARDS


def _copy_graph(graph):
    clone = Graph()
    for prefix, namespace in graph.namespaces():
        clone.bind(prefix, namespace)
    for triple in graph:
        clone.add(triple)
    return clone


def candidates(engine, ingredient, targets):
    """Return role matches with no known failure or audit under target standards.

    The current rules cannot establish a Pass; each match includes its actual
    provisional statuses and must not be presented as verified compliance.
    """
    targets = tuple(targets)
    if not targets or any(target not in STANDARDS for target in targets):
        raise ValueError("Choose at least one supported target standard.")
    roles = set(engine.graph.objects(ingredient, FOOD.hasFunctionalRole))
    matches = []
    for alternative in engine.ingredients():
        if alternative == ingredient or not roles.intersection(engine.graph.objects(alternative, FOOD.hasFunctionalRole)):
            continue
        graph = _copy_graph(engine.graph)
        probe = URIRef(f"urn:substitution-probe:{uuid4()}")
        graph.add((probe, RDF.type, FOOD.FoodProduct))
        graph.add((probe, FOOD.containsIngredient, alternative))
        result = KnowledgeEngine(graph).evaluate(probe)
        statuses = {target: result[target]["status"] for target in targets}
        if all(status not in ("Fail", "Audit Required") for status in statuses.values()):
            matches.append((alternative, statuses))
    return matches


def simulate(engine, product, original, alternative):
    """Replace every reachable occurrence, re-evaluating on a graph copy."""
    if original == alternative:
        raise ValueError("Select a different replacement.")
    if (alternative, RDF.type, FOOD.Ingredient) not in engine.graph:
        raise ValueError("Replacement must be an ingredient in the graph.")
    parents = {parent for parent, child in engine.ingredient_edges(product) if child == original}
    if not parents:
        raise ValueError("The original ingredient is not in this product.")
    descendants = {child for _, child in engine.ingredient_edges(alternative)} | {alternative}
    if parents & descendants:
        raise ValueError("This replacement would create a cycle.")
    graph = _copy_graph(engine.graph)
    for parent in parents:
        graph.remove((parent, FOOD.containsIngredient, original))
        graph.add((parent, FOOD.containsIngredient, alternative))
    return KnowledgeEngine(graph).evaluate(product)
