# Dietary Compliance Expert System

A Streamlit application that uses a knowledge graph and SPARQL rules to assess
food products against Halal, Kosher, Vegetarian, and Vegan standards. It traces
nested ingredients, explains findings, and suggests possible substitutions.

## Run locally

Requires Python 3.10 or newer.

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Open the URL printed by Streamlit.

## Use the app

- **Dashboard:** select a product to view its scorecard, supply chain,
  ingredient catalog, and reformulation options.
- **New Product / New Ingredient:** add custom data for the current session.
- **Tools & Export:** download the session graph, inferred graph, or audit report.
- **Ontology Graphs:** inspect the T-Box relationships or a product-focused
  A-Box graph.
- **Settings:** change the theme and text size.

Custom data is stored in the current session; export the graph to keep a copy.

## Project files

- `ontology/food_compliance_tbox.ttl` — ontology schema.
- `ontology/food_compliance_abox.ttl` — products, ingredients, and certificates.
- `rules/` — SPARQL inference and substitution rules.
- `src/` — graph loading, reasoning, queries, and visualization.
- `tests/` — automated tests and isolated graph fixtures.

## Tests

```sh
python -m unittest discover -s tests -v
```

## Deployment

Push the project to GitHub and create a Streamlit Community Cloud app using
`app.py` as the entry point. See the [Streamlit deployment guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy).

## Scope and limitations

Results depend on the supplied data and implemented rules. The system is a
project prototype and its results should not be treated as certification.
Allergen-Free assessment is not currently implemented. See
[TEAM_DISCUSSION.md](TEAM_DISCUSSION.md) for open policy questions and
[VALIDATION.md](VALIDATION.md) for remaining acceptance work. The earlier
[project specification](PROJECT_SPECIFICATION.md) is retained for reference.
