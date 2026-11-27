import importlib
import json
from pathlib import Path

import streamlit as st
from rdflib import Graph, RDF, RDFS, URIRef
from streamlit_agraph import Config, Edge, Node, agraph

import src.recipes as _recipes_mod
from src.graph_visualizer import abox_product_graph_data, edge_label, graph_data, ingredient_path, label, node_level, ontology_graph_data
from src.knowledge_engine import FOOD, KnowledgeEngine, KnowledgeGraphError, STANDARDS
from src.queries import query_substitutes, simulate_multi_reformulation
from src.reasoner import DietaryReasoner
from src.reformulation import candidates

if not hasattr(_recipes_mod.RecipeBuilder, "add_product"):
    importlib.reload(_recipes_mod)
RecipeBuilder = _recipes_mod.RecipeBuilder


ROOT = Path(__file__).resolve().parent

MENU_PAGES = (
    "Dashboard",
    "New Product",
    "New Ingredient",
    "Tools & Export",
    "Ontology Graphs",
    "Settings",
)

THEME_PALETTES = {
    "Dark": {
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
        "alert_error_bg": "#3b161b",
        "alert_error_border": "#7f1d1d",
        "alert_error_text": "#fecaca",
        "alert_warning_bg": "#362810",
        "alert_warning_border": "#78350f",
        "alert_warning_text": "#fde68a",
        "alert_success_bg": "#0f2e1f",
        "alert_success_border": "#14532d",
        "alert_success_text": "#bbf7d0",
        "alert_info_bg": "#13263d",
        "alert_info_border": "#1e3a5f",
        "alert_info_text": "#bae6fd",
        "nodes": {
            "product": "#2563eb",
            "ingredient": "#d97706",
            "flagged": "#dc2626",
            "origin": "#475569",
            "certificate": "#16a34a",
        },
    },
    "Light": {
        "bg": "#f8fafc",
        "surface": "#ffffff",
        "card_bg": "#ffffff",
        "sidebar_bg": "#f1f5f9",
        "text": "#0f172a",
        "muted": "#475569",
        "border": "#cbd5e1",
        "accent": "#0284c7",
        "edge_color": "#475569",
        "edge_font_color": "#0f172a",
        "edge_stroke": "#ffffff",
        "node_font_color": "#ffffff",
        "alert_error_bg": "#fef2f2",
        "alert_error_border": "#fecaca",
        "alert_error_text": "#991b1b",
        "alert_warning_bg": "#fffbeb",
        "alert_warning_border": "#fde68a",
        "alert_warning_text": "#92400e",
        "alert_success_bg": "#f0fdf4",
        "alert_success_border": "#bbf7d0",
        "alert_success_text": "#166534",
        "alert_info_bg": "#f0f9ff",
        "alert_info_border": "#bae6fd",
        "alert_info_text": "#075985",
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
    if theme_key not in THEME_PALETTES:
        theme_key = "Dark"
    if font_label not in FONT_SIZES:
        font_label = "Medium (16px)"
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
            --alert-error-bg: {palette['alert_error_bg']};
            --alert-error-border: {palette['alert_error_border']};
            --alert-error-text: {palette['alert_error_text']};
            --alert-warning-bg: {palette['alert_warning_bg']};
            --alert-warning-border: {palette['alert_warning_border']};
            --alert-warning-text: {palette['alert_warning_text']};
            --alert-success-bg: {palette['alert_success_bg']};
            --alert-success-border: {palette['alert_success_border']};
            --alert-success-text: {palette['alert_success_text']};
            --alert-info-bg: {palette['alert_info_bg']};
            --alert-info-border: {palette['alert_info_border']};
            --alert-info-text: {palette['alert_info_text']};
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
        /* Forms & Expanders */
        [data-testid="stForm"],
        [data-testid="stExpander"] {{
            background-color: var(--app-surface) !important;
            border: 1px solid var(--app-border) !important;
            border-radius: 6px !important;
        }}
        [data-testid="stExpander"] details,
        [data-testid="stExpander"] details > summary,
        [data-testid="stExpander"] [data-testid="stExpanderDetails"] {{
            background-color: var(--app-surface) !important;
            color: var(--app-text) !important;
        }}
        [data-testid="stExpander"] details > summary:hover {{
            background-color: var(--app-bg) !important;
        }}
        [data-testid="stExpander"] details > summary svg {{
            fill: var(--app-muted) !important;
            color: var(--app-muted) !important;
        }}
        /* Alerts (Error, Warning, Success, Info) */
        [data-testid="stAlert"] > div {{
            background-color: var(--app-surface) !important;
            border: 1px solid var(--app-border) !important;
            border-radius: 6px !important;
        }}
        [data-testid="stAlert"]:has([data-testid="stAlertContentError"]) > div,
        [data-testid="stAlert"] [data-baseweb="notification"]:has([data-testid="stAlertContentError"]) {{
            background-color: var(--alert-error-bg) !important;
            border: 1px solid var(--alert-error-border) !important;
        }}
        [data-testid="stAlertContentError"],
        [data-testid="stAlertContentError"] p,
        [data-testid="stAlertContentError"] span {{
            color: var(--alert-error-text) !important;
            font-weight: 600 !important;
        }}
        [data-testid="stAlert"]:has([data-testid="stAlertContentWarning"]) > div,
        [data-testid="stAlert"] [data-baseweb="notification"]:has([data-testid="stAlertContentWarning"]) {{
            background-color: var(--alert-warning-bg) !important;
            border: 1px solid var(--alert-warning-border) !important;
        }}
        [data-testid="stAlertContentWarning"],
        [data-testid="stAlertContentWarning"] p,
        [data-testid="stAlertContentWarning"] span {{
            color: var(--alert-warning-text) !important;
            font-weight: 600 !important;
        }}
        [data-testid="stAlert"]:has([data-testid="stAlertContentSuccess"]) > div,
        [data-testid="stAlert"] [data-baseweb="notification"]:has([data-testid="stAlertContentSuccess"]) {{
            background-color: var(--alert-success-bg) !important;
            border: 1px solid var(--alert-success-border) !important;
        }}
        [data-testid="stAlertContentSuccess"],
        [data-testid="stAlertContentSuccess"] p,
        [data-testid="stAlertContentSuccess"] span {{
            color: var(--alert-success-text) !important;
            font-weight: 600 !important;
        }}
        [data-testid="stAlert"]:has([data-testid="stAlertContentInfo"]) > div,
        [data-testid="stAlert"] [data-baseweb="notification"]:has([data-testid="stAlertContentInfo"]) {{
            background-color: var(--alert-info-bg) !important;
            border: 1px solid var(--alert-info-border) !important;
        }}
        [data-testid="stAlertContentInfo"],
        [data-testid="stAlertContentInfo"] p,
        [data-testid="stAlertContentInfo"] span {{
            color: var(--alert-info-text) !important;
            font-weight: 600 !important;
        }}
        /* Inputs, Selects, Popovers & Buttons */
        [data-baseweb="select"] > div,
        [data-baseweb="input"],
        [data-baseweb="input"] > div,
        [data-baseweb="base-input"],
        [data-baseweb="textarea"],
        [data-baseweb="textarea"] > div,
        .stTextInput input,
        .stTextArea textarea,
        .stNumberInput input {{
            background-color: var(--app-surface) !important;
            color: var(--app-text) !important;
            border-color: var(--app-border) !important;
            font-size: {base_px}px !important;
        }}
        [data-baseweb="select"] span,
        [data-baseweb="select"] input {{
            color: var(--app-text) !important;
        }}
        [data-baseweb="select"] svg,
        .stNumberInput button svg {{
            fill: var(--app-muted) !important;
            color: var(--app-muted) !important;
        }}
        [data-baseweb="popover"],
        [data-baseweb="popover"] ul,
        [data-baseweb="menu"],
        [role="listbox"] {{
            background-color: var(--app-surface) !important;
            color: var(--app-text) !important;
            border-color: var(--app-border) !important;
        }}
        [role="option"] {{
            background-color: var(--app-surface) !important;
            color: var(--app-text) !important;
        }}
        [role="option"]:hover,
        [role="option"][aria-selected="true"] {{
            background-color: var(--app-border) !important;
            color: var(--app-text) !important;
        }}
        .stButton > button,
        .stDownloadButton > button,
        [data-testid="stFormSubmitButton"] > button {{
            background-color: var(--app-surface) !important;
            color: var(--app-text) !important;
            border: 1px solid var(--app-border) !important;
            border-radius: 6px !important;
        }}
        .stButton > button:hover,
        .stDownloadButton > button:hover,
        [data-testid="stFormSubmitButton"] > button:hover {{
            background-color: var(--app-border) !important;
            border-color: var(--app-accent) !important;
        }}
        [data-testid="stMetricValue"],
        [data-testid="stMetricLabel"] {{
            color: var(--app-text) !important;
        }}
        /* Tabs */
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
        /* Clean flat summary block */
        .product-summary {{
            background: var(--app-surface);
            border: 1px solid var(--app-border);
            border-radius: 6px;
            padding: 12px 16px;
            margin-bottom: 12px;
        }}
        .product-summary-meta {{
            color: var(--app-muted) !important;
            font-size: {small_px}px !important;
            margin-top: 6px;
        }}
        .color-swatch {{
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 2px;
            margin-right: 6px;
            vertical-align: middle;
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


def _build_catalog_rows(engine: KnowledgeEngine) -> list[dict]:
    rows = []
    for ing in engine.ingredients():
        e_num = str(engine.graph.value(ing, FOOD.eNumber) or "—")
        eth = engine.graph.value(ing, FOOD.ethanolPercentage)
        eth_str = f"{float(eth):.1f}%" if eth is not None else "0.0%"
        origins_str = (
            ", ".join(label(engine.graph, o) for o in engine.graph.objects(ing, FOOD.derivedFrom))
            or "Unspecified"
        )
        roles_str = ", ".join(label(engine.graph, r) for r in engine.graph.objects(ing, FOOD.hasFunctionalRole)) or "—"
        certs_str = ", ".join(label(engine.graph, c) for c in engine.graph.objects(ing, FOOD.hasCertificate)) or "None"
        subs_str = (
            ", ".join(label(engine.graph, s) for s in engine.direct_ingredients(ing))
            or "—"
        )
        rows.append({
            "Ingredient": label(engine.graph, ing),
            "E-Number": e_num,
            "Origin": origins_str,
            "Role": roles_str,
            "Ethanol %": eth_str,
            "Certificates": certs_str,
            "Sub-ingredients": subs_str,
        })
    return rows


st.set_page_config(
    page_title="Dietary Compliance",
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

if (
    "recipe" not in st.session_state
    or st.session_state.recipe is None
    or not hasattr(st.session_state.recipe, "add_product")
    or not hasattr(st.session_state.recipe, "graph")
):
    st.session_state.recipe = RecipeBuilder(base_engine.graph)
else:
    for _triple in base_engine.graph:
        if _triple not in st.session_state.recipe.graph:
            st.session_state.recipe.graph.add(_triple)
if "selected_product" not in st.session_state:
    st.session_state.selected_product = FOOD.StrawberryGummyCandy
if "theme_choice" not in st.session_state or st.session_state.theme_choice not in THEME_PALETTES:
    st.session_state.theme_choice = "Dark"
if "font_choice" not in st.session_state or st.session_state.font_choice not in FONT_SIZES:
    st.session_state.font_choice = "Medium (16px)"

recipe: RecipeBuilder = st.session_state.recipe
engine = KnowledgeEngine(recipe.graph)
reasoner = DietaryReasoner(engine.graph)
products = engine.products()

# =====================================================================
# SIDEBAR
# =====================================================================
st.sidebar.markdown("### Dietary Compliance")
active_page = st.sidebar.radio("Menu", MENU_PAGES)

palette = _apply_theme_and_typography(st.session_state.theme_choice, st.session_state.font_choice)
node_font_px = FONT_SIZES[st.session_state.font_choice]

st.sidebar.divider()
st.sidebar.caption(
    f"Products: {len(products)} · Ingredients: {len(engine.ingredients())} · Triples: {len(engine.graph)}"
)
if recipe.owned:
    st.sidebar.info(f"Custom items: {len(recipe.owned)}")

# =====================================================================
# PAGE 1: DASHBOARD
# =====================================================================
if active_page == "Dashboard":
    st.title("Dietary Compliance Dashboard")
    st.caption("Check product ingredients against Halal, Kosher, Vegetarian, and Vegan rules.")

    if not products:
        st.warning("No products found in the graph.")
        st.stop()

    if st.session_state.selected_product not in products:
        st.session_state.selected_product = products[0]
    if "dashboard_product" not in st.session_state or st.session_state.dashboard_product not in products:
        st.session_state.dashboard_product = st.session_state.selected_product

    def remember_product_selection():
        st.session_state.selected_product = st.session_state.dashboard_product

    top_col1, top_col2 = st.columns([1, 2])
    with top_col1:
        product = st.selectbox(
            "Product",
            products,
            format_func=lambda node: label(engine.graph, node),
            key="dashboard_product",
            on_change=remember_product_selection,
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
        ings_text = ", ".join(direct_ings) if direct_ings else "None"
        st.markdown(
            f"""
            <div class="product-summary">
                <div><strong>{label(engine.graph, product)}</strong></div>
                <div>Direct ingredients ({len(direct_ings)}): {ings_text}</div>
                <div class="product-summary-meta">Sub-ingredients: {len(reachable_ings)} · Flagged: {len(flagged_all)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    tab_scorecard, tab_explorer, tab_reformulate, tab_catalog = st.tabs([
        "Scorecard",
        "Supply Chain",
        "Reformulation",
        "Ingredients",
    ])

    with tab_scorecard:
        st.subheader("Scorecard")
        columns = st.columns(len(STANDARDS))
        for column, standard in zip(columns, STANDARDS):
            result = results[standard]
            with column:
                st.subheader(label(engine.graph, standard))
                _render_status_badge(result["status"])

        st.subheader("Issues")
        issues = [(standard, issue) for standard in STANDARDS for issue in results[standard]["issues"]]
        if not issues:
            st.write("No compliance issues found.")
        for standard, issue in issues:
            with st.expander(f"{label(engine.graph, standard)}: {issue['message']}", expanded=True):
                for ingredient in issue["ingredients"]:
                    path = ingredient_path(engine, product, ingredient)
                    st.write(
                        " → ".join(label(engine.graph, node) for node in path)
                        if path
                        else label(engine.graph, ingredient)
                    )

    with tab_explorer:
        st.subheader("Supply chain graph")
        nodes, edges = graph_data(engine, product, flagged_all)
        levels = node_level(product, nodes, edges)
        st.caption("Blue: Product · Amber: Ingredient · Red: Flagged · Slate: Origin · Green: Certificate")
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
                st.caption(f"E-Number: {e_num}")
            for predicate, value in sorted(engine.graph.predicate_objects(node), key=lambda pair: tuple(map(str, pair))):
                if predicate == RDFS.label:
                    continue
                st.write(f"**{label(engine.graph, predicate)}:** {label(engine.graph, value)}")

    with tab_reformulate:
        st.subheader("Reformulation")
        st.caption("Substitutes share the same functional role and pass all selected standards.")
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
            st.info("This product passes all selected standards.")
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
                st.info("No matching substitutes found.")
            else:
                st.write("Available substitutes:")
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

                # Drop sub-ingredients that are only reachable through a parent compound ingredient already in batch_plan
                planned_keys = set(batch_plan)
                effective_plan: dict[URIRef, URIRef] = {}
                for ing, rep in batch_plan.items():
                    visited = {product}
                    stack = [product]
                    reachable_without_other_planned = False
                    while stack:
                        curr = stack.pop()
                        for child in engine.direct_ingredients(curr):
                            if child == ing:
                                reachable_without_other_planned = True
                                break
                            if child not in visited and child not in planned_keys:
                                visited.add(child)
                                stack.append(child)
                        if reachable_without_other_planned:
                            break
                    if reachable_without_other_planned:
                        effective_plan[ing] = rep
                batch_plan = effective_plan

                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    run_single = st.button("Simulate reformulation")
                with btn_col2:
                    run_batch = len(batch_plan) > 1 and st.button("Simulate all replacements")

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
                        st.subheader("Before vs. After")
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

    with tab_catalog:
        st.subheader("Ingredient catalog")
        st.dataframe(_build_catalog_rows(engine), width="stretch", hide_index=True)

# =====================================================================
# PAGE 2: NEW PRODUCT
# =====================================================================
elif active_page == "New Product":
    st.title("New Product")
    st.caption("Add a product to this session and select its ingredients.")

    ingredient_options = engine.ingredients()
    with st.form("new_product_form"):
        prod_name = st.text_input("Product name", placeholder="e.g. Berry Tart")
        prod_comment = st.text_area(
            "Notes (optional)",
            placeholder="Short product description or label note",
        )
        selected_ings = st.multiselect(
            "Ingredients",
            ingredient_options,
            format_func=lambda node: label(engine.graph, node),
        )
        create_prod = st.form_submit_button("Create product")

    if create_prod:
        try:
            new_prod = recipe.add_product(prod_name, ingredients=selected_ings, comment=prod_comment)
            st.session_state.selected_product = new_prod
            st.success(f"Created **{label(recipe.graph, new_prod)}**.")
        except ValueError as exc:
            st.error(str(exc))

    st.subheader("Products")
    prod_rows = []
    for prod in engine.products():
        eval_res = reasoner.evaluate_product(prod)
        direct = [label(engine.graph, i) for i in engine.direct_ingredients(prod)]
        prod_rows.append({
            "Product": label(engine.graph, prod),
            "Source": "Custom" if prod in recipe.owned else "Default",
            "Ingredients": ", ".join(direct) or "None",
            "Halal": eval_res[FOOD.Halal]["status"],
            "Kosher": eval_res[FOOD.Kosher]["status"],
            "Vegetarian": eval_res[FOOD.Vegetarian]["status"],
            "Vegan": eval_res[FOOD.Vegan]["status"],
        })
    st.dataframe(prod_rows, width="stretch", hide_index=True)

# =====================================================================
# PAGE 3: NEW INGREDIENT
# =====================================================================
elif active_page == "New Ingredient":
    st.title("New Ingredient")
    st.caption("Add an ingredient with its label, origin, role, and certificates.")

    origin_options = _available_origins(engine.graph)
    role_options = [None] + _available_roles(engine.graph)
    cert_options = _available_certificates(engine.graph)
    ingredient_options = engine.ingredients()
    parent_targets = [None] + engine.products() + sorted(
        [node for node in recipe.owned if (node, RDF.type, FOOD.Ingredient) in engine.graph],
        key=str,
    )
    default_parent_idx = (
        parent_targets.index(recipe.product)
        if recipe.product in parent_targets
        else 0
    )

    with st.form("new_ingredient_form"):
        col_id1, col_id2 = st.columns([2, 1])
        with col_id1:
            ing_name = st.text_input("Ingredient name", placeholder="e.g. Berry Extract")
        with col_id2:
            e_number = st.text_input("E-Number", placeholder="e.g. E440 (optional)")
        ing_comment = st.text_input(
            "Notes (optional)",
            placeholder="Supplier or label note",
        )

        col_prop1, col_prop2 = st.columns(2)
        with col_prop1:
            selected_origins = st.multiselect(
                "Origins",
                origin_options,
                format_func=lambda node: label(engine.graph, node),
                help="Leave empty if the origin is unknown. Unknown origins trigger a Halal audit.",
            )
        with col_prop2:
            selected_role = st.selectbox(
                "Functional role",
                role_options,
                format_func=lambda node: "None" if node is None else label(engine.graph, node),
            )

        col_eth1, col_eth2 = st.columns([1, 2])
        with col_eth1:
            specify_ethanol = st.checkbox("Set ethanol percentage")
        with col_eth2:
            ethanol = st.number_input("Ethanol % (v/v)", min_value=0.0, max_value=100.0, value=0.0)

        selected_certs = st.multiselect(
            "Certificates",
            cert_options,
            format_func=lambda node: label(engine.graph, node),
        )
        sub_ings = st.multiselect(
            "Sub-ingredients (optional)",
            ingredient_options,
            format_func=lambda node: label(engine.graph, node),
        )
        parent_node = st.selectbox(
            "Add to product or ingredient (optional)",
            parent_targets,
            index=default_parent_idx,
            format_func=lambda node: "None (catalog only)" if node is None else label(engine.graph, node),
        )

        save_ing = st.form_submit_button("Save ingredient")

    if save_ing:
        try:
            created = recipe.add_ingredient(
                parent_node,
                ing_name,
                ethanol if specify_ethanol else None,
                role=selected_role,
                certificates=selected_certs,
                origins=selected_origins,
                e_number=e_number,
                comment=ing_comment,
                sub_ingredients=sub_ings,
            )
            st.success(f"Saved **{label(recipe.graph, created)}**.")
        except ValueError as exc:
            st.error(str(exc))

    with st.expander("Link existing ingredient"):
        with st.form("link_existing_ingredient_form"):
            link_targets = engine.products() + sorted(
                [node for node in recipe.owned if (node, RDF.type, FOOD.Ingredient) in engine.graph],
                key=str,
            )
            link_parent = st.selectbox(
                "Parent",
                link_targets,
                format_func=lambda node: label(engine.graph, node),
            )
            link_child = st.selectbox(
                "Ingredient",
                ingredient_options,
                format_func=lambda node: label(engine.graph, node),
            )
            do_link = st.form_submit_button("Link ingredient")
        if do_link:
            try:
                recipe.link_ingredient(link_parent, link_child)
                st.success(f"Linked **{label(recipe.graph, link_child)}** to **{label(recipe.graph, link_parent)}**.")
            except ValueError as exc:
                st.error(str(exc))

    st.subheader("Ingredient catalog")
    st.dataframe(_build_catalog_rows(engine), width="stretch", hide_index=True)

# =====================================================================
# PAGE 4: TOOLS & EXPORT
# =====================================================================
elif active_page == "Tools & Export":
    st.title("Tools & Export")
    st.caption("Download data or reset custom session changes.")

    enriched_graph = reasoner.materialize()
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    m_col1.metric("Products", len(products))
    m_col2.metric("Ingredients", len(engine.ingredients()))
    m_col3.metric("Base Triples", len(engine.graph))
    m_col4.metric("Inferred Triples", len(enriched_graph))

    st.subheader("Export")
    exp_col1, exp_col2, exp_col3 = st.columns(3)
    with exp_col1:
        st.download_button(
            "Export Graph (.ttl)",
            data=engine.graph.serialize(format="turtle"),
            file_name="food_compliance_session.ttl",
            mime="text/turtle",
        )
    with exp_col2:
        st.download_button(
            "Export Inferred Graph (.ttl)",
            data=enriched_graph.serialize(format="turtle"),
            file_name="food_compliance_materialized.ttl",
            mime="text/turtle",
        )
    with exp_col3:
        audit_payload = {
            label(engine.graph, prod): {
                label(engine.graph, std): {
                    "status": res["status"],
                    "issues": [issue["message"] for issue in res["issues"]],
                }
                for std, res in reasoner.evaluate_product(prod).items()
            }
            for prod in products
        }
        st.download_button(
            "Export Audit Report (.json)",
            data=json.dumps(audit_payload, indent=2),
            file_name="food_compliance_audit.json",
            mime="application/json",
        )

    st.subheader("Session data")
    if st.button("Reset session data"):
        st.session_state.recipe = RecipeBuilder(base_engine.graph)
        st.session_state.selected_product = FOOD.StrawberryGummyCandy
        st.rerun()

# =====================================================================
# PAGE 5: ONTOLOGY GRAPHS
# =====================================================================
elif active_page == "Ontology Graphs":
    st.title("Ontology Graphs")
    button_col1, button_col2 = st.columns(2)
    with button_col1:
        if st.button("Show TBox Graph"):
            st.session_state.ontology_graph_choice = "tbox"
    with button_col2:
        if st.button("Show ABox Graph"):
            st.session_state.ontology_graph_choice = "abox"

    if st.session_state.get("ontology_graph_choice"):
        ontology_file = (
            "food_compliance_tbox.ttl" if st.session_state.ontology_graph_choice == "tbox"
            else "food_compliance_abox.ttl"
        )
        ontology_graph = Graph().parse(ROOT / "ontology" / ontology_file, format="turtle")
        if st.session_state.ontology_graph_choice == "abox":
            abox_engine = KnowledgeEngine(ontology_graph)
            abox_products = abox_engine.products()
            if not abox_products:
                st.warning("No products found in the A-Box.")
                st.stop()
            abox_product = st.selectbox(
                "A-Box product", abox_products,
                format_func=lambda node: label(ontology_graph, node),
                key="abox_graph_product",
            )
            ontology_nodes, ontology_edges = abox_product_graph_data(abox_engine, abox_product)
            st.caption("Showing the selected product's ingredients, origins, certificates, and roles.")
        else:
            ontology_nodes, ontology_edges = ontology_graph_data(ontology_graph)
        st.caption(
            f"Showing asserted data from {ontology_file}: {len(ontology_nodes)} nodes and "
            f"{len(ontology_edges)} relationships. "
            "RDF and OWL vocabulary nodes, session changes, and inferred statements are hidden."
        )
        selected_ontology_node = agraph(
            nodes=[
                Node(
                    id=node.n3(),
                    label=label(ontology_graph, node),
                    title=str(node),
                    color=palette["nodes"]["product"],
                    shape="box",
                    font={"color": palette["node_font_color"], "size": node_font_px},
                )
                for node in ontology_nodes
            ],
            edges=[
                Edge(source=source.n3(), target=target.n3(), label=edge_label(ontology_graph, predicate),
                     color=palette["edge_color"],
                     font={"color": palette["edge_font_color"], "strokeColor": palette["edge_stroke"],
                           "strokeWidth": 3})
                for source, predicate, target in ontology_edges
            ],
            config=Config(height=650, width="100%", directed=True, physics=True),
        )
        selected_term = next((node for node in ontology_nodes if node.n3() == selected_ontology_node), None)
        if selected_term is not None:
            st.write(f"**Selected:** {label(ontology_graph, selected_term)}")
            st.code(str(selected_term))

# =====================================================================
# PAGE 6: SETTINGS
# =====================================================================
elif active_page == "Settings":
    st.title("Settings")
    st.caption("Set the color theme and text size.")

    theme_options = list(THEME_PALETTES.keys())
    font_options = list(FONT_SIZES.keys())

    new_theme = st.radio(
        "Theme",
        theme_options,
        index=theme_options.index(st.session_state.theme_choice),
        horizontal=True,
    )
    new_font = st.selectbox(
        "Font size",
        font_options,
        index=font_options.index(st.session_state.font_choice),
    )

    if new_theme != st.session_state.theme_choice or new_font != st.session_state.font_choice:
        st.session_state.theme_choice = new_theme
        st.session_state.font_choice = new_font
        st.rerun()

    st.subheader("Node colors")
    st.markdown(
        f"""
        <div class="product-summary">
            <div><span class="color-swatch" style="background:{palette['nodes']['product']}"></span>Product ({palette['nodes']['product']})</div>
            <div><span class="color-swatch" style="background:{palette['nodes']['ingredient']}"></span>Ingredient ({palette['nodes']['ingredient']})</div>
            <div><span class="color-swatch" style="background:{palette['nodes']['flagged']}"></span>Flagged ({palette['nodes']['flagged']})</div>
            <div><span class="color-swatch" style="background:{palette['nodes']['origin']}"></span>Origin ({palette['nodes']['origin']})</div>
            <div><span class="color-swatch" style="background:{palette['nodes']['certificate']}"></span>Certificate ({palette['nodes']['certificate']})</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
