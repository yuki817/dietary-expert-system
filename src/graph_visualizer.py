"""Prepare the supply-chain graph and paths for presentation."""

from collections import deque

from rdflib import Literal, RDFS

from src.knowledge_engine import FOOD


def label(graph, node):
    if isinstance(node, Literal):
        return str(node)
    return str(graph.value(node, RDFS.label) or graph.namespace_manager.normalizeUri(node))


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
