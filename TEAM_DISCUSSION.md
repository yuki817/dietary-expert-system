# Team discussion: requirements & Member 2 Reasoning Specification

These questions come from the current README. Below are the finalized Member 2 (Reasoning & Backend Engineer) decisions implemented in `rules/kosher.sparql`, `rules/vegan_veg.sparql`, `rules/substitution_rules.sparql`, `src/reasoner.py`, and `src/queries.py`, along with the technical report section for Reasoning Rules.

## 1. Artisan Dough Bread: porcine-derived L-cysteine

- **Decision and expected results:** Any ingredient derived from `AnimalOrigin` (`Porcine`, `Bovine`, `Poultry`, `Marine`, `Insect`) or `MeatTissue`, `AnimalFat`, `AnimalEnzyme` triggers non-compliance for both **Vegetarian** and **Vegan** in `rules/vegan_veg.sparql`. If Artisan Dough Bread uses porcine-derived `LCysteine` (`E920`), it fails Halal, Kosher, Vegetarian, and Vegan; once reformulated with `MicrobialTransglutaminase` via the Reformulation Advisor, it passes all four standards.

## 2. Beef Cheese Burger: Halal result

- **Decision and expected results:** When a product triggers both `food:isNonCompliantWith` (`Fail`) and `food:requiresAuditFor` (`Audit Required`), `Fail` takes precedence as the overall standard status while all inferred `food:ComplianceIssue` nodes remain attached and visible in the diagnostic report. For the Beef Cheese Burger benchmark to evaluate to **Audit Required** for Halal, its bun uses synthetic/plant L-cysteine (or unconditioned flour) while its beef patty is uncertified `Bovine`.

## 3. Kosher certification requirements

- **Decision and expected results:** In `rules/kosher.sparql`:
  1. **Treif origins:** `food:Porcine`, `food:Marine` (shellfish), and `food:Insect` trigger `food:isNonCompliantWith food:Kosher`.
  2. **Animal derivatives certification:** Any ingredient derived from `AnimalOrigin`, `Bovine`, `Poultry`, `AnimalFat`, `AnimalEnzyme`, or `MeatTissue` without a linked `food:KosherCert` triggers `food:isNonCompliantWith food:Kosher`.
  3. **Basar BeChalav:** Co-occurrence of meat (`MeatTissue`, `Bovine`, `Poultry`) and dairy (`Dairy`, `Whey`, `Casein`, `Cheese`) in the transitive ingredient tree triggers `food:isNonCompliantWith food:Kosher`.

## 4. Allergen-Free standard

- **Decision and expected results:** Scoped out of the 4 core scorecard columns (`Halal`, `Kosher`, `Vegetarian`, `Vegan`) in the 3-day sprint benchmark matrix.

## 5. Unknown information and substitutions

- **Decision and expected results:**
  - **Pass inference (`food:isCompliantWith`):** In `DietaryReasoner.materialize()` (`src/reasoner.py`), a product is inferred `food:isCompliantWith` a standard if and only if: (a) it has at least one ingredient, (b) every reachable leaf ingredient has a declared `food:derivedFrom` biological/byproduct origin (missing origins trigger `food:requiresAuditFor`), and (c) no `isNonCompliantWith` or `requiresAuditFor` rule fired for that standard.
  - **Substitution rule (`rules/substitution_rules.sparql` & `src/queries.py`):** `substitution_rules.sparql` constructs `food:hasSuggestedSubstitute` links between ingredients sharing `food:hasFunctionalRole` where the substitute derives from `PlantOrigin`, `MicrobialOrigin`, or `SyntheticOrigin`, has no animal derivatives, and has ethanol $\le 0.5\%$. `query_substitutes()` and `simulate_reformulation()` verify that the candidate and the entire reformulated product achieve `Pass` across all selected target standards.

## 6. Shared modeling and rule assumptions

- **Decision:** All SPARQL rules use `rdf:type/rdfs:subClassOf*` property paths for zero-JVM taxonomy traversal and deterministic `SHA256(...)` issue IRIs so repeated inference executions are 100% idempotent. Ethanol threshold fails strictly above `0.5%` (`FILTER(?ethanol > 0.5)`).

---

## Member 2 Technical Report Draft: Section 3 — Reasoning Rules & Inference Architecture

### 3.1 Pure-Python In-Memory Semantic Reasoning Pipeline (`src/reasoner.py`)
The inference engine (`DietaryReasoner`) uses `rdflib` to parse the OWL/RDFS T-Box and A-Box Turtle graphs into memory and executes five modular `SPARQL CONSTRUCT` rule sets without requiring an external JVM triple store:

1. **Halal Haram Rule (`rules/halal.sparql`):** Traverses transitive ingredient trees via `food:containsIngredient+` and flags products containing `food:Porcine` or `food:Insect` origins, or any ingredient with `food:ethanolPercentage > 0.5`.
2. **Halal Mashbooh Audit Rule (`rules/halal_audit.sparql`):** Flags products containing permissible animal derivatives (`food:Bovine`, `food:Poultry`, `food:AnimalEnzyme`) that lack a linked `food:HalalCert` (`FILTER NOT EXISTS`), asserting `food:requiresAuditFor food:Halal`.
3. **Kosher Compliance Rule (`rules/kosher.sparql`):** Combines three declarative checks in a single `CONSTRUCT` query: (a) *Treif* origins (`Porcine`, `Marine`, `Insect`), (b) uncertified animal derivatives lacking `food:KosherCert`, and (c) *Basar BeChalav* (meat and dairy co-occurrence across `MeatTissue`/`Bovine`/`Poultry` and `Dairy`/`Whey`/`Casein`/`Cheese`).
4. **Vegetarian & Vegan Rule (`rules/vegan_veg.sparql`):** Flags all `AnimalOrigin` subclasses and slaughter byproducts (`MeatTissue`, `AnimalFat`, `AnimalEnzyme`) as non-compliant with both `food:Vegetarian` and `food:Vegan`, and flags non-meat animal byproducts (`Dairy`, `Whey`, `Casein`, `Cheese`, `Egg`, `Honey`) as non-compliant with `food:Vegan`.
5. **Functional Substitution Rule (`rules/substitution_rules.sparql`):** Infers `?flaggedIng food:hasSuggestedSubstitute ?substitute` by matching `food:hasFunctionalRole` across distinct ingredients where the candidate is derived exclusively from `PlantOrigin`, `MicrobialOrigin`, or `SyntheticOrigin` and contains $\le 0.5\%$ ethanol.

### 3.2 Closed-World Completeness & `SPARQL SELECT` Query Layer (`src/queries.py`)
After running all `CONSTRUCT` rules, `DietaryReasoner.materialize()` performs a completeness check on every product's leaf ingredients: if any leaf ingredient lacks a `food:derivedFrom` assertion, an `Audit Required` issue is generated; otherwise, standards with zero failures or audits are explicitly asserted as `food:isCompliantWith` (**Pass**). The query module (`src/queries.py`) exposes pure `SPARQL SELECT` interfaces for all three application views:
- `query_compliance_scorecard()`: Queries inferred compliance statuses and diagnostic `food:ComplianceIssue` nodes.
- `query_supply_chain_trace()`: Executes `food:containsIngredient*` and `food:containsIngredient+` property-path queries to extract parent-child BOM edges, biological origins, and certificates.
- `query_substitutes()` & `simulate_reformulation()`: Queries inferred `food:hasSuggestedSubstitute` edges and validates whole-product compliance on an isolated graph clone.

## Follow-up

- [x] Record the decisions and owners above.
- [x] Implement full SPARQL CONSTRUCT rules (`rules/kosher.sparql`, `rules/vegan_veg.sparql`, `rules/substitution_rules.sparql`).
- [x] Implement `src/reasoner.py` and `src/queries.py`.
- [x] Turn the agreed examples and edge cases into acceptance tests (`tests/test_sparql_rules.py`, `tests/test_reasoner.py`, `tests/test_queries.py`).
