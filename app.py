from pathlib import Path
import runpy

import streamlit as st
from rdflib import RDF, RDFS, URIRef
from streamlit_agraph import Config, Edge, Node, agraph

from src.graph_visualizer import edge_label, graph_data, ingredient_path, label, node_level
from src.knowledge_engine import FOOD, KnowledgeEngine, KnowledgeGraphError, STANDARDS
from src.queries import query_substitutes, simulate_multi_reformulation
from src.reasoner import DietaryReasoner
from src.recipes import RecipeBuilder
from src.reformulation import candidates, simulate


ROOT = Path(__file__).resolve().parent
COLORS = {
    "product": "#2563eb",
    "ingredient": "#f59e0b",
    "flagged": "#dc2626",
    "origin": "#6b7280",
    "certificate": "#16a34a",
}


def _render_status_badge(status: str) -> None:
    if status == "Fail":
        st.error(status)
    elif status == "Audit Required":
        st.warning(status)
    elif status == "Pass":
        st.success(status)
    else:
        st.info(status)


def _available_origins(graph) -> list[URIRef]:
    origins = set()
    for cls in (
        FOOD.PlantOrigin, FOOD.MicrobialOrigin, FOOD.SyntheticOrigin,
        FOOD.Porcine, FOOD.Bovine, FOOD.Poultry, FOOD.Marine, FOOD.Insect,
        FOOD.MeatTissue, FOOD.AnimalFat, FOOD.AnimalEnzyme, FOOD.Dairy, FOOD.Egg, FOOD.Honey,
    ):
        origins.update(graph.subjects(RDF.type, cls))
    return sorted(origins, key=str)


def _available_roles(graph) -> list[URIRef]:
    return sorted(graph.subjects(RDF.type, FOOD.FunctionalRole), key=str)


def _available_certificates(graph) -> list[URIRef]:
    certs = set(graph.subjects(RDF.type, FOOD.HalalCert)) | set(graph.subjects(RDF.type, FOOD.KosherCert))
    return sorted(certs, key=str)


st.set_page_config(page_title="Food Compliance Expert System", page_icon="🍽️")
page = st.sidebar.radio(
    "Choose a use case",
    ("Compliance scorecard", "Supply chain explorer", "Reformulation advisor", "Sample page"),
)

if page == "Sample page":
    runpy.run_path(str(ROOT / "sample.py"))
    st.stop()

st.title("Food Compliance Expert System")
st.write("Explore dietary compliance and ingredient supply chains.")

try:
    base_engine = KnowledgeEngine.from_turtle(
        ROOT / "ontology/food_compliance_tbox.ttl", ROOT / "ontology/food_compliance_abox.ttl",
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
    st.sidebar.caption("Changes stay in this browser session. Assign an origin or link catalog ingredients to verify compliance.")
    with st.sidebar.form("add_ingredient"):
        parents = sorted(recipe.owned, key=str)
        parent = st.selectbox("Add under", parents, format_func=lambda node: label(recipe.graph, node))
        mode = st.radio("Ingredient", ("Create new", "Link existing"))
        name = st.text_input("New ingredient name")
        specify_ethanol = st.checkbox("Set ethanol percentage")
        ethanol = st.number_input("Ethanol percentage", min_value=0.0, max_value=100.0, value=0.0)
        origin_options = [None] + _available_origins(recipe.graph)
        selected_origin = st.selectbox(
            "Biological origin (optional)",
            origin_options,
            format_func=lambda node: "Unspecified (triggers audit)" if node is None else label(recipe.graph, node),
        )
        role_options = [None] + _available_roles(recipe.graph)
        selected_role = st.selectbox(
            "Functional role (optional)",
            role_options,
            format_func=lambda node: "None" if node is None else label(recipe.graph, node),
        )
        cert_options = _available_certificates(recipe.graph)
        selected_certs = st.multiselect(
            "Certificates (optional)",
            cert_options,
            format_func=lambda node: label(recipe.graph, node),
        )
        ingredient_options = KnowledgeEngine(recipe.graph).ingredients()
        existing = st.selectbox("Existing ingredient", ingredient_options,
                                format_func=lambda node: label(recipe.graph, node))
        add = st.form_submit_button("Add ingredient")
    if add:
        try:
            if mode == "Create new":
                recipe.add_ingredient(
                    parent,
                    name,
                    ethanol if specify_ethanol else None,
                    origin=selected_origin,
                    role=selected_role,
                    certificates=selected_certs,
                )
            else:
                recipe.link_ingredient(parent, existing)
            st.rerun()
        except ValueError as exc:
            st.sidebar.error(str(exc))

engine = KnowledgeEngine(st.session_state.recipe.graph) if st.session_state.recipe else base_engine
reasoner = DietaryReasoner(engine.graph)
products = engine.products()
if not products:
    st.warning("No products were found in the knowledge graph.")
    st.stop()

st.caption("Evaluated with declarative OWL/RDFS & SPARQL CONSTRUCT compliance rules across Halal, Kosher, Vegetarian, and Vegan standards.")
default_choice = st.session_state.recipe.product if st.session_state.recipe else FOOD.StrawberryGummyCandy
default_product = products.index(default_choice) if default_choice in products else 0
product = st.selectbox("Product", products, index=default_product,
                       format_func=lambda node: label(engine.graph, node))
results = reasoner.evaluate_product(product)

if page == "Compliance scorecard":
    st.header("Compliance scorecard")
    columns = st.columns(len(STANDARDS))
    for column, standard in zip(columns, STANDARDS):
        result = results[standard]
        with column:
            st.subheader(label(engine.graph, standard))
            _render_status_badge(result["status"])
    st.subheader("Findings")
    issues = [(standard, issue) for standard in STANDARDS for issue in results[standard]["issues"]]
    if not issues:
        st.write("All ingredients and biological origins verified compliant with zero violations.")
    for standard, issue in issues:
        with st.expander(f"{label(engine.graph, standard)}: {issue['message']}"):
            for ingredient in issue["ingredients"]:
                path = ingredient_path(engine, product, ingredient)
                st.write(" → ".join(label(engine.graph, node) for node in path) if path else label(engine.graph, ingredient))
elif page == "Supply chain explorer":
    st.header("Supply chain explorer")
    flagged = {ingredient for result in results.values() for issue in result["issues"]
               for ingredient in issue["ingredients"]}
    nodes, edges = graph_data(engine, product, flagged)
    levels = node_level(product, nodes, edges)
    st.caption(
        "🔵 **Blue**: Product · 🟠 **Amber**: Ingredient · 🔴 **Red**: Flagged Ingredient · "
        "⚪ **Slate**: Biological Origin · 🟢 **Green**: Certificate"
    )
    selected = agraph(
        nodes=[
            Node(
                id=str(node),
                label=label(engine.graph, node),
                title=f"{label(engine.graph, node)} ({kind})",
                color=COLORS[kind],
                shape="box",
                level=levels.get(node, 1),
                margin=10,
                font={"color": "#ffffff", "size": 14, "face": "Inter, system-ui, sans-serif"},
                borderWidth=2,
                shadow=True,
            )
            for node, kind in sorted(nodes.items(), key=lambda item: str(item[0]))
        ],
        edges=[
            Edge(
                source=str(source),
                target=str(target),
                label=edge_label(engine.graph, predicate),
                color="#94a3b8",
                font={
                    "color": "#e2e8f0",
                    "size": 11,
                    "strokeWidth": 3,
                    "strokeColor": "#0f172a",
                    "align": "horizontal",
                },
                smooth={"type": "cubicBezier", "forceDirection": "vertical", "roundness": 0.4},
            )
            for source, target, predicate in edges
        ],
        config=Config(
            height=560,
            width="100%",
            directed=True,
            physics=False,
            hierarchical=True,
            direction="UD",
            sortMethod="directed",
            levelSeparation=115,
            nodeSpacing=190,
            treeSpacing=210,
        ),
    )
    choices = sorted(nodes, key=str)
    selected_node = URIRef(selected) if isinstance(selected, str) else None
    default = choices.index(selected_node) if selected_node in nodes else 0
    node = st.selectbox("Node details", choices, index=default,
                        format_func=lambda item: label(engine.graph, item))
    node_kind = nodes.get(node, "node").capitalize()
    st.markdown(f"#### {label(engine.graph, node)} (`{node_kind}`)")
    e_num = engine.graph.value(node, FOOD.eNumber)
    if e_num:
        st.caption(f"INS / E-Number: {e_num}")
    for predicate, value in sorted(engine.graph.predicate_objects(node), key=lambda pair: tuple(map(str, pair))):
        if predicate == RDFS.label:
            continue
        st.write(f"**{label(engine.graph, predicate)}:** {label(engine.graph, value)}")
else:
    st.header("Reformulation advisor")
    st.caption("Matches share the same functional role and satisfy all target dietary standards.")
    targets = st.multiselect("Target standards", STANDARDS, default=list(STANDARDS),
                             format_func=lambda standard: label(engine.graph, standard))
    flagged = sorted({ingredient for standard in targets for issue in results[standard]["issues"]
                      for ingredient in issue["ingredients"]}, key=str)
    if not targets:
        st.info("Select at least one target standard.")
    elif not flagged:
        st.info("This product already passes all selected target standards.")
    else:
        enriched_graph = reasoner.materialize()
        original = st.selectbox("Flagged ingredient", flagged,
                                format_func=lambda node: label(engine.graph, node))
        sparql_matches = query_substitutes(enriched_graph, original, targets)
        matches = [(item["substitute"], item["statuses"]) for item in sparql_matches] or candidates(engine, original, targets)
        if not matches:
            st.info("No role matches without a known failure or audit were found.")
        else:
            st.write("Recommended functional role substitutes:")
            for alternative, statuses in matches:
                st.write(f"{label(engine.graph, alternative)} — " + ", ".join(
                    f"{label(engine.graph, standard)}: {status}" for standard, status in statuses.items()
                ))
            replacement = st.selectbox("Replacement", [item[0] for item in matches],
                                       format_func=lambda node: label(engine.graph, node))

            # Prepare complete batch plan when multiple ingredients are flagged
            batch_plan: dict[URIRef, URIRef] = {original: replacement}
            for other_ing in flagged:
                if other_ing == original:
                    continue
                other_subs = query_substitutes(enriched_graph, other_ing, targets)
                if other_subs:
                    batch_plan[other_ing] = other_subs[0]["substitute"]

            if st.button("Simulate reformulation"):
                try:
                    simulated = simulate_multi_reformulation(reasoner, product, {original: replacement})
                    st.subheader("Simulated product results")
                    for standard in STANDARDS:
                        st.write(f"{label(engine.graph, standard)}: {simulated[standard]['status']}")
                        for issue in simulated[standard]["issues"]:
                            st.write(f"• {issue['message']}")
                except ValueError as exc:
                    st.error(str(exc))

            if len(batch_plan) > 1 and st.button("Simulate complete product reformulation (all flagged ingredients)"):
                try:
                    batch_simulated = simulate_multi_reformulation(reasoner, product, batch_plan)
                    st.subheader("Complete Reformulation Plan (Before vs. After)")
                    for orig_ing, rep_ing in batch_plan.items():
                        st.write(f"• Replace **{label(engine.graph, orig_ing)}** → **{label(engine.graph, rep_ing)}**")
                    cols = st.columns(len(STANDARDS))
                    for col, standard in zip(cols, STANDARDS):
                        with col:
                            st.caption(f"{label(engine.graph, standard)} (Before: {results[standard]['status']})")
                            _render_status_badge(batch_simulated[standard]["status"])
                except ValueError as exc:
                    st.error(str(exc))
