import streamlit as st
from rdflib import Graph, Namespace, Literal
from rdflib.namespace import RDF, RDFS
from pathlib import Path

from src.graph_visualizer import label
from src.knowledge_engine import KnowledgeEngine
from src.reasoner import DietaryReasoner

FOOD = Namespace("http://example.org/food-compliance#")

@st.cache_resource
def load_base_graph():
    root = Path(__file__).resolve().parent
    return KnowledgeEngine.from_turtle(
        root / "ontology/food_compliance_tbox.ttl",
        root / "ontology/food_compliance_abox.ttl",
    ).graph

def run_inference(base_graph, target_product_uri):
    """Evaluate product with the complete DietaryReasoner rule engine."""
    assessment = DietaryReasoner(base_graph).evaluate_product(target_product_uri)
    results = {label(base_graph, standard): result["status"]
               for standard, result in assessment.items()}
    issues = []
    for standard, result in assessment.items():
        for issue in result["issues"]:
            issues.append({
                "standard": label(base_graph, standard),
                "ingredient": ", ".join(label(base_graph, ing) for ing in issue["ingredients"]),
                "reason": issue["message"],
            })

    return results, issues

# --- UI LAYOUT ---
st.title("🥗 Multi-Standard Dietary & Supply Chain Compliance Expert System")
st.caption("Evaluated with declarative OWL/RDFS & SPARQL CONSTRUCT compliance rules.")
tab1, tab2, tab3 = st.tabs([
    "1. Compliance Matrix & Audit",
    "2. Supply Chain Traceability",
    "3. Reformulation Advisor"
])

base_g = load_base_graph()

# Fetch available products and ingredients from A-Box
products = {
    str(base_g.value(p, RDFS.label)): p
    for p in base_g.subjects(RDF.type, FOOD.FoodProduct)
}
ingredients = {
    str(base_g.value(i, RDFS.label)): i
    for i in base_g.subjects(RDF.type, FOOD.Ingredient)
}

with tab1:
    st.subheader("Step 1: Choose Evaluation Mode")
    input_mode = st.radio(
        "Select how you want to test a product:",
        ["Select Benchmark Product (A-Box)", "Assemble Custom Recipe (Dynamic A-Box)"],
        horizontal=True
    )

    working_graph = base_g
    selected_product_uri = None

    if input_mode == "Select Benchmark Product (A-Box)":
        selected_name = st.selectbox("Choose a Food Product:", list(products.keys()))
        selected_product_uri = products[selected_name]

        # Show direct ingredients
        direct_ings = [
            str(base_g.value(ing, RDFS.label))
            for ing in base_g.objects(selected_product_uri, FOOD.containsIngredient)
        ]
        st.info(f"**Direct Ingredients:** {', '.join(direct_ings)}")

    else:
        col_name, col_ings = st.columns([1, 2])
        with col_name:
            custom_name = st.text_input("Custom Product Name:", value="Custom Trial Product")
        with col_ings:
            chosen_ing_names = st.multiselect(
                "Select Ingredients & Additives:",
                options=list(ingredients.keys()),
                default=[]
            )

        # Dynamically instantiate a new FoodProduct node in a temporary graph
        working_graph = Graph()
        for t in base_g:
            working_graph.add(t)

        selected_product_uri = FOOD["CustomProduct_Runtime"]
        working_graph.add((selected_product_uri, RDF.type, FOOD.FoodProduct))
        working_graph.add((selected_product_uri, RDFS.label, Literal(custom_name)))
        for ing_name in chosen_ing_names:
            working_graph.add((selected_product_uri, FOOD.containsIngredient, ingredients[ing_name]))

    st.divider()

    if selected_product_uri:
        status_map, flagged_issues = run_inference(working_graph, selected_product_uri)

        st.subheader("Step 2: Multi-Standard Compliance Scorecard")
        cols = st.columns(4)
        for idx, (std, status) in enumerate(status_map.items()):
            with cols[idx]:
                if status == "Audit Required":
                    st.warning(f"### {std}\n**⚠️ AUDIT REQUIRED**")
                elif status == "Fail":
                    st.error(f"### {std}\n**❌ NON-COMPLIANT**")
                elif status == "Pass":
                    st.success(f"### {std}\n**✅ COMPLIANT (PASS)**")
                else:
                    st.info(f"### {std}\n**NOT ASSESSED**")

        st.subheader("Step 3: Diagnostic Explanation (Fired Rules)")
        if not flagged_issues:
            st.success("All ingredients and biological origins verified compliant with zero violations.")
        else:
            for item in flagged_issues:
                with st.expander(f"[{item['standard']}] Flagged: {item['ingredient']}", expanded=True):
                    st.write(f"**Rule Explanation:** {item['reason']}")

with tab2:
    st.info("Use the Supply chain explorer in the sidebar to view the interactive graph.")

with tab3:
    st.info("Use the Reformulation advisor in the sidebar to simulate substitutions.")
