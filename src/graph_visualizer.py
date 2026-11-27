"""Prepare the supply-chain graph and paths for presentation."""

from collections import deque

from rdflib import Literal, OWL, RDF, RDFS, URIRef, XSD

from src.knowledge_engine import FOOD


FRIENDLY_LABELS = {
    RDF.type: "Type",
    RDFS.label: "Label",
    RDFS.subClassOf: "Subclass of",
    FOOD.containsIngredient: "contains ingredient",
    FOOD.derivedFrom: "derived from",
    FOOD.hasCertificate: "has certificate",
    FOOD.hasFunctionalRole: "has functional role",
    FOOD.ethanolPercentage: "ethanol percentage (% v/v)",
    FOOD.eNumber: "INS / E-Number",
    FOOD.Halal: "Halal",
    FOOD.Kosher: "Kosher",
    FOOD.Vegetarian: "Vegetarian",
    FOOD.Vegan: "Vegan",
    FOOD.FoodProduct: "Food Product",
    FOOD.Ingredient: "Ingredient",
}

SHORT_EDGE_LABELS = {
    FOOD.containsIngredient: "contains",
    FOOD.derivedFrom: "derived from",
    FOOD.hasCertificate: "certified by",
}


def label(graph, node):
    if isinstance(node, Literal):
        return str(node)
    explicit = graph.value(node, RDFS.label)
    if explicit:
        return str(explicit)
    if node in FRIENDLY_LABELS:
        return FRIENDLY_LABELS[node]
    raw = str(graph.namespace_manager.normalizeUri(node))
    if raw.startswith("food:"):
        return raw.split(":", 1)[1]
    return raw


def edge_label(graph, predicate):
    if predicate in SHORT_EDGE_LABELS:
        return SHORT_EDGE_LABELS[predicate]
    return label(graph, predicate)


def ontology_graph_data(graph, include_literals=False):
    """Return domain relationships without RDF/OWL vocabulary nodes."""
    nodes = set()
    edges = []
    vocabulary_namespaces = tuple(map(str, (RDF, RDFS, OWL, XSD)))
    for source, predicate, target in graph:
        if isinstance(target, Literal) and not include_literals:
            continue
        if any(
            isinstance(node, URIRef) and str(node).startswith(vocabulary_namespaces)
            for node in (source, target)
        ):
            continue
        nodes.add(source)
        nodes.add(target)
        edges.append((source, predicate, target))
    return sorted(nodes, key=lambda node: node.n3()), sorted(
        edges, key=lambda edge: tuple(node.n3() for node in edge)
    )


def node_level(root, nodes, edges):
    """Compute BFS hierarchy depth from the root product so vis.js lays out top-to-bottom cleanly."""
    adj = {node: [] for node in nodes}
    for source, target, _ in edges:
        adj.setdefault(source, []).append(target)
    levels = {root: 0}
    queue = deque([root])
    while queue:
        current = queue.popleft()
        for child in adj.get(current, []):
            if child not in levels:
                levels[child] = levels[current] + 1
                queue.append(child)
    for node in nodes:
        levels.setdefault(node, 1)
    return levels


def ingredient_path(engine, root, target):
    """Return one shortest direct ingredient path, or an empty list."""
    queue = deque([(root, [root])])
    visited = {root}
    while queue:
        node, path = queue.popleft()
        if node == target:
            return path
        for child in engine.direct_ingredients(node):
            if child not in visited:
                visited.add(child)
                queue.append((child, path + [child]))
    return []


def graph_data(engine, root, flagged):
    """Return display nodes and direct edges including sources and certificates."""
    ingredient_edges = engine.ingredient_edges(root)
    ingredients = {root}
    for parent, child in ingredient_edges:
        ingredients.update((parent, child))
    nodes = {node: "product" if node == root else "ingredient" for node in ingredients}
    edges = [(parent, child, FOOD.containsIngredient) for parent, child in ingredient_edges]
    for ingredient in ingredients:
        for predicate, kind in ((FOOD.derivedFrom, "origin"), (FOOD.hasCertificate, "certificate")):
            for related in engine.graph.objects(ingredient, predicate):
                nodes.setdefault(related, kind)
                edges.append((ingredient, related, predicate))
    for node in flagged:
        if node in nodes and node != root:
            nodes[node] = "flagged"
    return nodes, sorted(edges, key=lambda edge: tuple(map(str, edge)))


def abox_product_graph_data(engine, product):
    """Return one product's ingredient chain and directly related domain nodes."""
    nodes, edges = graph_data(engine, product, set())
    for ingredient, kind in list(nodes.items()):
        if kind != "ingredient":
            continue
        for role in engine.graph.objects(ingredient, FOOD.hasFunctionalRole):
            nodes.setdefault(role, "role")
            edges.append((ingredient, FOOD.hasFunctionalRole, role))
    return sorted(nodes, key=lambda node: node.n3()), sorted(
        edges, key=lambda edge: tuple(node.n3() for node in edge)
    )
