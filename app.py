from pathlib import Path

import streamlit as st
from rdflib import URIRef
from streamlit_agraph import Config, Edge, Node, agraph

from src.graph_visualizer import graph_data, ingredient_path, label
from src.knowledge_engine import FOOD, KnowledgeEngine, KnowledgeGraphError, STANDARDS
from src.recipes import RecipeBuilder


ROOT = Path(__file__).resolve().parent
COLORS = {
    "product": "#2563eb",
    "ingredient": "#f59e0b",
    "flagged": "#dc2626",
    "origin": "#6b7280",
    "certificate": "#16a34a",
}

st.set_page_config(page_title="Food Compliance Expert System", page_icon="🍽️")
st.title("Food Compliance Expert System")
st.write("Explore dietary compliance and ingredient supply chains.")
page = st.sidebar.radio(
    "Choose a use case",
    ("Compliance scorecard", "Supply chain explorer", "Reformulation advisor"),
)

if page == "Reformulation advisor":
    st.header("Reformulation advisor")
    st.info("Ingredient suggestions and reformulation simulation are coming soon.")
    st.stop()

try:
    base_engine = KnowledgeEngine.from_turtle(
        ROOT / "ontology/sample_tbox.ttl", ROOT / "ontology/sample_abox.ttl"
    )
except KnowledgeGraphError as exc:
    st.error(str(exc))
    st.stop()

st.sidebar.subheader("Custom recipe")
if "recipe" not in st.session_state:
    st.session_state.recipe = None

if st.session_state.recipe is None:
    with st.sidebar.form("new_recipe"):
        recipe_name = st.text_input("Recipe name")
        create_recipe = st.form_submit_button("Create recipe")
    if create_recipe:
        try:
            st.session_state.recipe = RecipeBuilder(base_engine.graph, recipe_name)
            st.rerun()
        except ValueError as exc:
            st.sidebar.error(str(exc))
else:
    recipe = st.session_state.recipe
    st.sidebar.write(f"Editing: {label(recipe.graph, recipe.product)}")
    if st.sidebar.button("Discard custom recipe"):
        st.session_state.recipe = None
        st.rerun()
    st.sidebar.caption("Changes stay in this browser session. Custom ingredients have no origin unless linked to catalog ingredients.")
    with st.sidebar.form("add_ingredient"):
        parents = sorted(recipe.owned, key=str)
        parent = st.selectbox("Add under", parents, format_func=lambda node: label(recipe.graph, node))
        mode = st.radio("Ingredient", ("Create new", "Link existing"))
        name = st.text_input("New ingredient name")
        specify_ethanol = st.checkbox("Set ethanol percentage")
        ethanol = st.number_input("Ethanol percentage", min_value=0.0, max_value=100.0, value=0.0)
        candidates = KnowledgeEngine(recipe.graph).ingredients()
        existing = st.selectbox("Existing ingredient", candidates,
                                format_func=lambda node: label(recipe.graph, node))
        add = st.form_submit_button("Add ingredient")
    if add:
        try:
            if mode == "Create new":
                recipe.add_ingredient(parent, name, ethanol if specify_ethanol else None)
            else:
                recipe.link_ingredient(parent, existing)
            st.rerun()
        except ValueError as exc:
            st.sidebar.error(str(exc))

engine = KnowledgeEngine(st.session_state.recipe.graph) if st.session_state.recipe else base_engine
products = engine.products()
if not products:
    st.warning("No products were found in the knowledge graph.")
    st.stop()

st.caption("Illustrative sample data and provisional rules; not a complete compliance assessment.")
default_product = products.index(st.session_state.recipe.product) if st.session_state.recipe else 0
product = st.selectbox("Product", products, index=default_product,
                       format_func=lambda node: label(engine.graph, node))
results = engine.evaluate(product)

if page == "Compliance scorecard":
    st.header("Compliance scorecard")
    columns = st.columns(len(STANDARDS))
    for column, standard in zip(columns, STANDARDS):
        result = results[standard]
        with column:
            st.subheader(label(engine.graph, standard))
            if result["status"] == "Fail":
                st.error(result["status"])
            elif result["status"] == "Audit Required":
                st.warning(result["status"])
            else:
                st.info(result["status"])
    st.subheader("Findings")
    issues = [(standard, issue) for standard in STANDARDS for issue in results[standard]["issues"]]
    if not issues:
        st.write("No findings from the current rules.")
    for standard, issue in issues:
        with st.expander(f"{label(engine.graph, standard)}: {issue['message']}"):
            for ingredient in issue["ingredients"]:
                path = ingredient_path(engine, product, ingredient)
                st.write(" → ".join(label(engine.graph, node) for node in path) if path else label(engine.graph, ingredient))
else:
    st.header("Supply chain explorer")
    flagged = {ingredient for result in results.values() for issue in result["issues"]
               for ingredient in issue["ingredients"]}
    nodes, edges = graph_data(engine, product, flagged)
    st.caption("Blue: product · Orange: ingredient · Red: flagged ingredient · Grey: origin · Green: certificate")
    selected = agraph(
        nodes=[Node(id=str(node), label=label(engine.graph, node), color=COLORS[kind])
               for node, kind in sorted(nodes.items(), key=lambda item: str(item[0]))],
        edges=[Edge(source=str(source), target=str(target), label=label(engine.graph, predicate))
               for source, target, predicate in edges],
        config=Config(height=500, directed=True, hierarchical=True),
    )
    choices = sorted(nodes, key=str)
    selected_node = URIRef(selected) if isinstance(selected, str) else None
    default = choices.index(selected_node) if selected_node in nodes else 0
    node = st.selectbox("Node details", choices, index=default,
                        format_func=lambda item: label(engine.graph, item))
    st.write(f"**{label(engine.graph, node)}**")
    for predicate, value in sorted(engine.graph.predicate_objects(node), key=lambda pair: tuple(map(str, pair))):
        st.write(f"{label(engine.graph, predicate)}: {label(engine.graph, value)}")
