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
from src.reformulation import candidates


ROOT = Path(__file__).resolve().parent

# High-contrast node palettes tailored for Light (Day) and Dark (Night) themes
THEME_PALETTES = {
    "🌙 Dark (Night)": {
        "bg": "#0f172a",
        "surface": "#1e293b",
        "card_bg": "#1e293b",
        "sidebar_bg": "#0b1120",
        "text": "#f8fafc",
        "muted": "#cbd5e1",
        "border": "#334155",
        "accent": "#38bdf8",
        "edge_color": "#94a3b8",
        "edge_font_color": "#f1f5f9",
        "edge_stroke": "#0f172a",
        "node_font_color": "#ffffff",
        "nodes": {
            "product": "#2563eb",
            "ingredient": "#d97706",
            "flagged": "#dc2626",
            "origin": "#475569",
            "certificate": "#16a34a",
        },
    },
    "🌞 Light (Day)": {
        "bg": "#f8fafc",
        "surface": "#ffffff",
        "card_bg": "#ffffff",
        "sidebar_bg": "#f1f5f9",
        "text": "#0f172a",
        "muted": "#334155",
        "border": "#cbd5e1",
        "accent": "#0284c7",
        "edge_color": "#475569",
        "edge_font_color": "#0f172a",
        "edge_stroke": "#ffffff",
        "node_font_color": "#ffffff",
        "nodes": {
            "product": "#1d4ed8",
            "ingredient": "#b45309",
            "flagged": "#b91c1c",
            "origin": "#334155",
            "certificate": "#15803d",
        },
    },
}

FONT_SIZES = {
    "Small (14px)": 14,
    "Medium (16px)": 16,
    "Large (18px)": 18,
    "Extra Large (20px)": 20,
}


def _apply_theme_and_typography(theme_key: str, font_label: str) -> dict:
    palette = THEME_PALETTES[theme_key]
    base_px = FONT_SIZES[font_label]
    h1_px = int(base_px * 1.95)
    h2_px = int(base_px * 1.45)
    h3_px = int(base_px * 1.2)
    small_px = max(12, base_px - 2)

    st.markdown(
        f"""
        <style>
        :root {{
            --app-bg: {palette['bg']};
            --app-surface: {palette['surface']};
            --app-card: {palette['card_bg']};
            --app-sidebar: {palette['sidebar_bg']};
            --app-text: {palette['text']};
            --app-muted: {palette['muted']};
            --app-border: {palette['border']};
            --app-accent: {palette['accent']};
            --app-font-size: {base_px}px;
        }}
        .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
            background-color: var(--app-bg) !important;
            color: var(--app-text) !important;
            font-size: var(--app-font-size) !important;
        }}
        [data-testid="stSidebar"], [data-testid="stSidebarContent"] {{
            background-color: var(--app-sidebar) !important;
            color: var(--app-text) !important;
            border-right: 1px solid var(--app-border) !important;
        }}
        .stApp h1 {{
            font-size: {h1_px}px !important;
            color: var(--app-text) !important;
            font-weight: 700 !important;
            letter-spacing: -0.02em;
        }}
        .stApp h2 {{
            font-size: {h2_px}px !important;
            color: var(--app-text) !important;
            font-weight: 650 !important;
        }}
        .stApp h3, .stApp h4 {{
            font-size: {h3_px}px !important;
            color: var(--app-text) !important;
            font-weight: 600 !important;
        }}
        .stApp p, .stApp li, .stApp label, .stApp span,
        [data-testid="stMarkdownContainer"] p,
        [data-testid="stMarkdownContainer"] li,
        [data-testid="stWidgetLabel"] p {{
            font-size: {base_px}px !important;
            color: var(--app-text) !important;
            line-height: 1.55 !important;
        }}
        [data-testid="stCaptionContainer"] p {{
            font-size: {small_px}px !important;
            color: var(--app-muted) !important;
        }}
        /* Selects, inputs, forms, and expanders */
        [data-testid="stForm"], [data-testid="stExpander"] {{
            background-color: var(--app-surface) !important;
            border: 1px solid var(--app-border) !important;
            border-radius: 10px !important;
        }}
        [data-baseweb="select"] > div,
        [data-baseweb="input"] > div,
        [data-baseweb="base-input"] {{
            background-color: var(--app-surface) !important;
            color: var(--app-text) !important;
            border-color: var(--app-border) !important;
            font-size: {base_px}px !important;
        }}
        /* Tabs bar styling */
        button[data-baseweb="tab"] {{
            font-size: {base_px}px !important;
            font-weight: 600 !important;
            color: var(--app-muted) !important;
            padding: 10px 18px !important;
        }}
        button[data-baseweb="tab"][aria-selected="true"] {{
            color: var(--app-accent) !important;
            border-bottom-color: var(--app-accent) !important;
        }}
        /* Custom KPI & metadata cards */
        .kg-banner {{
            background: var(--app-surface);
            border: 1px solid var(--app-border);
            border-left: 5px solid var(--app-accent);
            border-radius: 12px;
            padding: 16px 20px;
            margin-bottom: 16px;
        }}
        .kg-pill {{
            display: inline-block;
            background: var(--app-surface);
            color: var(--app-text);
            border: 1px solid var(--app-border);
            border-radius: 999px;
            padding: 3px 12px;
            margin: 2px 6px 2px 0;
            font-size: {small_px}px;
            font-weight: 500;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
    return palette


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


st.set_page_config(
    page_title="Food Compliance Expert System",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded",
)

try:
    base_engine = KnowledgeEngine.from_turtle(
        ROOT / "ontology/food_compliance_tbox.ttl", ROOT / "ontology/food_compliance_abox.ttl",
    )
except KnowledgeGraphError as exc:
    st.error(str(exc))
    st.stop()

if "recipe" not in st.session_state:
    st.session_state.recipe = None

# =====================================================================
# SIDEBAR: Navigation, Theme & Font Settings, New Product, New Ingredient
# =====================================================================
st.sidebar.markdown("### 🧭 Workspace & Controls")
nav_mode = st.sidebar.radio(
    "Workspace view",
    ("Unified Compliance Dashboard", "Legacy Sample Page"),
    label_visibility="collapsed",
)

st.sidebar.divider()
st.sidebar.subheader("🎨 Display & Accessibility")
theme_choice = st.sidebar.radio(
    "Theme mode",
    ("🌙 Dark (Night)", "🌞 Light (Day)"),
    horizontal=True,
)
font_choice = st.sidebar.selectbox(
    "Font size",
    list(FONT_SIZES.keys()),
    index=1,
)

palette = _apply_theme_and_typography(theme_choice, font_choice)
node_font_px = FONT_SIZES[font_choice]

if nav_mode == "Legacy Sample Page":
    runpy.run_path(str(ROOT / "sample.py"))
    st.stop()

st.sidebar.divider()
st.sidebar.subheader("➕ New Product (Custom Recipe)")
if st.session_state.recipe is None:
    with st.sidebar.form("new_recipe"):
        recipe_name = st.text_input("Recipe name", placeholder="e.g. Vegan Berry Tart")
        create_recipe = st.form_submit_button("Create recipe")
    if create_recipe:
        try:
            st.session_state.recipe = RecipeBuilder(base_engine.graph, recipe_name)
            st.rerun()
        except ValueError as exc:
            st.sidebar.error(str(exc))
else:
    recipe = st.session_state.recipe
    st.sidebar.success(f"Active product: **{label(recipe.graph, recipe.product)}**")
    if st.sidebar.button("Discard custom recipe"):
        st.session_state.recipe = None
        st.rerun()

st.sidebar.divider()
st.sidebar.subheader("🧪 New Ingredient & BOM Linker")
if st.session_state.recipe is None:
    st.sidebar.caption("Create a New Product above first to add or link custom ingredients into its supply chain.")
else:
    recipe = st.session_state.recipe
    st.sidebar.caption("Add new ingredients (with origin, role, ethanol %, or certificates) or link catalog ingredients.")
    with st.sidebar.form("add_ingredient"):
        parents = sorted(recipe.owned, key=str)
        parent = st.selectbox("Add under", parents, format_func=lambda node: label(recipe.graph, node))
        mode = st.radio("Ingredient mode", ("Create new", "Link existing"), horizontal=True)
        name = st.text_input("New ingredient name", placeholder="e.g. fermented extract")
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
        existing = st.selectbox(
            "Existing ingredient",
            ingredient_options,
            format_func=lambda node: label(recipe.graph, node),
        )
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

st.sidebar.divider()
st.sidebar.subheader("💡 Knowledge Graph Tools")
st.sidebar.caption(
    f"**Products:** {len(products)} · **Ingredients:** {len(engine.ingredients())} · **Triples:** {len(engine.graph)}"
)
st.sidebar.download_button(
    "⬇️ Export Active Graph (.ttl)",
    data=engine.graph.serialize(format="turtle"),
    file_name="food_compliance_session.ttl",
    mime="text/turtle",
)

# =====================================================================
# MAIN PAGE: Unified Header, Product Bar, and All Menus in One View
# =====================================================================
st.title("🍽️ Multi-Standard Dietary & Supply Chain Compliance Expert System")
st.caption(
    "Semantic Web Knowledge Graph & Declarative SPARQL CONSTRUCT Reasoning Engine "
    "— Auditing Halal, Kosher, Vegetarian, and Vegan Supply Chains"
)

default_choice = st.session_state.recipe.product if st.session_state.recipe else FOOD.StrawberryGummyCandy
default_product = products.index(default_choice) if default_choice in products else 0

top_col1, top_col2 = st.columns([1, 2])
with top_col1:
    product = st.selectbox(
        "Product",
        products,
        index=default_product,
        format_func=lambda node: label(engine.graph, node),
    )

results = reasoner.evaluate_product(product)
direct_ings = [label(engine.graph, ing) for ing in engine.direct_ingredients(product)]
all_edges = engine.ingredient_edges(product)
reachable_ings = {child for _, child in all_edges}
flagged_all = {
    ingredient
    for result in results.values()
    for issue in result["issues"]
    for ingredient in issue["ingredients"]
}

with top_col2:
    pills_html = "".join(f'<span class="kg-pill">{name}</span>' for name in direct_ings) or "<em>None declared</em>"
    st.markdown(
        f"""
        <div class="kg-banner">
            <strong>Selected Product:</strong> {label(engine.graph, product)}<br/>
            <strong>Direct Ingredients ({len(direct_ings)}):</strong> {pills_html}<br/>
            <small>Total Transitive Sub-Ingredients: <strong>{len(reachable_ings)}</strong> ·
            Flagged Ingredients: <strong>{len(flagged_all)}</strong></small>
        </div>
        """,
        unsafe_allow_html=True,
    )

tab_scorecard, tab_explorer, tab_reformulate, tab_catalog = st.tabs([
    "📊 1. Compliance Scorecard & Audit",
    "🔗 2. Supply Chain Traceability Explorer",
    "🧪 3. Reformulation Advisor & Simulator",
    "📚 4. Ontology Ingredient Catalog",
])

# ---------------------------------------------------------------------
# TAB 1: Compliance Scorecard & Diagnostic Findings
# ---------------------------------------------------------------------
with tab_scorecard:
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
        with st.expander(f"{label(engine.graph, standard)}: {issue['message']}", expanded=True):
            for ingredient in issue["ingredients"]:
                path = ingredient_path(engine, product, ingredient)
                st.write(
                    " → ".join(label(engine.graph, node) for node in path)
                    if path
                    else label(engine.graph, ingredient)
                )

# ---------------------------------------------------------------------
# TAB 2: Supply Chain Traceability Explorer (Side-by-Side Graph + Details)
# ---------------------------------------------------------------------
with tab_explorer:
    st.header("Supply chain explorer")
    nodes, edges = graph_data(engine, product, flagged_all)
    levels = node_level(product, nodes, edges)
    st.caption(
        "🔵 **Blue**: Product · 🟠 **Amber**: Ingredient · 🔴 **Red**: Flagged Ingredient · "
        "⚪ **Slate**: Biological Origin · 🟢 **Green**: Certificate"
    )
    graph_col, detail_col = st.columns([2.2, 1])
    with graph_col:
        selected = agraph(
            nodes=[
                Node(
                    id=str(node),
                    label=label(engine.graph, node),
                    title=f"{label(engine.graph, node)} ({kind})",
                    color=palette["nodes"][kind],
                    shape="box",
                    level=levels.get(node, 1),
                    margin=10,
                    font={
                        "color": palette["node_font_color"],
                        "size": node_font_px,
                        "face": "Inter, system-ui, sans-serif",
                    },
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
                    color=palette["edge_color"],
                    font={
                        "color": palette["edge_font_color"],
                        "size": max(11, node_font_px - 3),
                        "strokeWidth": 3,
                        "strokeColor": palette["edge_stroke"],
                        "align": "horizontal",
                    },
                    smooth={"type": "cubicBezier", "forceDirection": "vertical", "roundness": 0.35},
                )
                for source, target, predicate in edges
            ],
            config=Config(
                height=540,
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
    with detail_col:
        choices = sorted(nodes, key=str)
        selected_node = URIRef(selected) if isinstance(selected, str) else None
        default = choices.index(selected_node) if selected_node in nodes else 0
        node = st.selectbox(
            "Node details",
            choices,
            index=default,
            format_func=lambda item: label(engine.graph, item),
        )
        node_kind = nodes.get(node, "node").capitalize()
        st.markdown(f"#### {label(engine.graph, node)} (`{node_kind}`)")
        e_num = engine.graph.value(node, FOOD.eNumber)
        if e_num:
            st.caption(f"INS / E-Number: {e_num}")
        for predicate, value in sorted(engine.graph.predicate_objects(node), key=lambda pair: tuple(map(str, pair))):
            if predicate == RDFS.label:
                continue
            st.write(f"**{label(engine.graph, predicate)}:** {label(engine.graph, value)}")

# ---------------------------------------------------------------------
# TAB 3: Reformulation Advisor & Simulator
# ---------------------------------------------------------------------
with tab_reformulate:
    st.header("Reformulation advisor")
    st.caption("Matches share the same functional role and satisfy all target dietary standards.")
    targets = st.multiselect(
        "Target standards",
        STANDARDS,
        default=list(STANDARDS),
        format_func=lambda standard: label(engine.graph, standard),
    )
    flagged = sorted(
        {
            ingredient
            for standard in targets
            for issue in results[standard]["issues"]
            for ingredient in issue["ingredients"]
        },
        key=str,
    )
    if not targets:
        st.info("Select at least one target standard.")
    elif not flagged:
        st.info("This product already passes all selected target standards.")
    else:
        enriched_graph = reasoner.materialize()
        original = st.selectbox(
            "Flagged ingredient",
            flagged,
            format_func=lambda node: label(engine.graph, node),
        )
        sparql_matches = query_substitutes(enriched_graph, original, targets)
        matches = [(item["substitute"], item["statuses"]) for item in sparql_matches] or candidates(
            engine, original, targets
        )
        if not matches:
            st.info("No role matches without a known failure or audit were found.")
        else:
            st.write("Recommended functional role substitutes:")
            for alternative, statuses in matches:
                st.write(
                    f"{label(engine.graph, alternative)} — "
                    + ", ".join(
                        f"{label(engine.graph, standard)}: {status}" for standard, status in statuses.items()
                    )
                )
            replacement = st.selectbox(
                "Replacement",
                [item[0] for item in matches],
                format_func=lambda node: label(engine.graph, node),
            )

            batch_plan: dict[URIRef, URIRef] = {original: replacement}
            for other_ing in flagged:
                if other_ing == original:
                    continue
                other_subs = query_substitutes(enriched_graph, other_ing, targets)
                if other_subs:
                    batch_plan[other_ing] = other_subs[0]["substitute"]

            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                run_single = st.button("Simulate reformulation")
            with btn_col2:
                run_batch = len(batch_plan) > 1 and st.button(
                    "Simulate complete product reformulation (all flagged ingredients)"
                )

            if run_single:
                try:
                    simulated = simulate_multi_reformulation(reasoner, product, {original: replacement})
                    st.subheader("Simulated product results")
                    for standard in STANDARDS:
                        st.write(f"{label(engine.graph, standard)}: {simulated[standard]['status']}")
                        for issue in simulated[standard]["issues"]:
                            st.write(f"• {issue['message']}")
                except ValueError as exc:
                    st.error(str(exc))

            if run_batch:
                try:
                    batch_simulated = simulate_multi_reformulation(reasoner, product, batch_plan)
                    st.subheader("Complete Reformulation Plan (Before vs. After)")
                    for orig_ing, rep_ing in batch_plan.items():
                        st.write(
                            f"• Replace **{label(engine.graph, orig_ing)}** → **{label(engine.graph, rep_ing)}**"
                        )
                    cols = st.columns(len(STANDARDS))
                    for col, standard in zip(cols, STANDARDS):
                        with col:
                            st.caption(f"{label(engine.graph, standard)} (Before: {results[standard]['status']})")
                            _render_status_badge(batch_simulated[standard]["status"])
                except ValueError as exc:
                    st.error(str(exc))

# ---------------------------------------------------------------------
# TAB 4: Ontology Ingredient & Certificate Knowledge Catalog
# ---------------------------------------------------------------------
with tab_catalog:
    st.header("Knowledge Graph Ingredient Catalog")
    st.caption("Complete A-Box catalog of ingredients, E-numbers, biological origins, functional roles, and certificates.")
    catalog_rows = []
    for ing in engine.ingredients():
        e_num = str(engine.graph.value(ing, FOOD.eNumber) or "—")
        eth = engine.graph.value(ing, FOOD.ethanolPercentage)
        eth_str = f"{float(eth):.1f}%" if eth is not None else "0.0%"
        origins_str = ", ".join(label(engine.graph, o) for o in engine.graph.objects(ing, FOOD.derivedFrom)) or "Compound / Unspecified"
        roles_str = ", ".join(label(engine.graph, r) for r in engine.graph.objects(ing, FOOD.hasFunctionalRole)) or "—"
        certs_str = ", ".join(label(engine.graph, c) for c in engine.graph.objects(ing, FOOD.hasCertificate)) or "None"
        catalog_rows.append({
            "Ingredient": label(engine.graph, ing),
            "E-Number": e_num,
            "Biological / Byproduct Origin": origins_str,
            "Functional Role": roles_str,
            "Ethanol %": eth_str,
            "Certificates": certs_str,
        })
    st.dataframe(catalog_rows, width="stretch", hide_index=True)
