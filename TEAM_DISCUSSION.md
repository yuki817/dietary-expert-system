# Team discussion: requirements to clarify

These questions come from the current README. Agree on each decision before treating the benchmark results as final, and update the README, ontology, data, and tests to match.

## 1. Artisan Dough Bread: porcine-derived L-cysteine

The benchmark says the bread contains L-cysteine derived from porcine sources, fails Halal and Kosher, but passes Vegetarian and Vegan. The stated vegetarian and vegan rules do not explicitly cover every animal-derived ingredient.

- Should any ingredient derived from an animal make a product non-vegetarian and non-vegan, or should only the listed byproduct classes count?
- Should the L-cysteine in this benchmark have a different source?
- **Decision and expected results:**

## 2. Beef Cheese Burger: Halal result

The burger includes a bun with L-cysteine. The bread example identifies its L-cysteine as porcine-derived, which would trigger a Halal failure, while the burger benchmark expects an audit for uncertified beef.

- Does the burger use the same L-cysteine instance and source as the bread?
- If both a failure and an audit apply, should the overall status be **Fail**, with both issues displayed?
- **Decision and expected results:**

## 3. Kosher certification requirements

The Kosher rule says animal or processed derivatives without valid Kosher certification fail. Some benchmark products expected to pass do not specify certificates for every potentially relevant ingredient.

- Which ingredients require certification, and is missing certification a failure or an audit?
- How is certificate validity represented and checked?
- Is every marine source prohibited, or only specific sources such as shellfish? How should the ontology distinguish them?
- **Decision and expected results:**

## 4. Allergen-Free standard

Allergen-Free is listed as a standard, but the README does not define allergens, rules, or benchmark results.

- Is this standard in scope for the sprint? If so, which allergens and declaration rules apply?
- Should users select specific allergens instead of receiving one general Allergen-Free result?
- **Decision and expected results:**

## 5. Unknown information and substitutions

The specification does not consistently say how missing origins, incomplete ingredient trees, or missing certificates affect a result. The substitution example checks source and role but does not verify every selected standard.

- When required information is missing, should the result be **Audit Required**? Which facts are mandatory for each standard?
- What conditions must a substitute meet for each selected standard, and should candidates requiring an audit be shown?
- Does a simulation pass only after the entire modified product is re-evaluated?
- **Decision and expected results:**

## 6. Shared modeling and rule assumptions

- Agree on the exact ontology names and representation of origins, byproducts, certificates, direct ingredient links, and functional roles.
- Confirm whether subclass inference is needed, and how it will be provided to the RDFLib rule engine.
- Confirm the intended scope and units of the 0.5% ethanol threshold, including the result at exactly 0.5%.
- **Decision:**

## Follow-up

- [ ] Record the decisions and owners above.
- [ ] Update the benchmark matrix and rule descriptions in README.md.
- [ ] Align the ontology and example data with the decisions.
- [ ] Turn the agreed examples and edge cases into acceptance tests.
