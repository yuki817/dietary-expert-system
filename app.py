import streamlit as st


st.set_page_config(page_title="Food Compliance Expert System", page_icon="🍽️")

st.title("Food Compliance Expert System")
st.write("Explore dietary compliance and ingredient supply chains.")

page = st.sidebar.radio(
    "Choose a use case",
    ("Compliance scorecard", "Supply chain explorer", "Reformulation advisor"),
)

if page == "Compliance scorecard":
    st.header("Compliance scorecard")
    st.info("Product selection and dietary compliance results are coming soon.")
elif page == "Supply chain explorer":
    st.header("Supply chain explorer")
    st.info("Ingredient traceability and graph visualization are coming soon.")
else:
    st.header("Reformulation advisor")
    st.info("Ingredient suggestions and reformulation simulation are coming soon.")
