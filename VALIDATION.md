# Validation and remaining acceptance work

The shipped graph contains fictional demonstration products, not the six-product
benchmark dataset. The dietary rules are provisional and `Not assessed` is not
a Pass. Do not use the demo results as an actual compliance determination.

## Checks available now

Run `python -m unittest discover -s tests -v` in the project virtual
environment. This checks graph loading and traversal, selected inference rules,
session-local recipes, role matching and simulation, plus Streamlit sample
workflows. Streamlit's application testing exercises the server-side UI; it
does not verify the interactive graph component visually in a browser.

On the development machine, one informal run on the sample graph measured
approximately 0.37 seconds for scorecard inference, 0.18 seconds for candidate
search, and 0.18 seconds for simulation. These are Python processing times,
not end-to-end UI timings or performance results for the final dataset.

## Before final acceptance

- [ ] Resolve the policy questions in `TEAM_DISCUSSION.md` and update the
  specification, rules, ontology, and expected results together.
- [ ] Integrate the team's final T-Box and A-Box; the app currently loads the
  two `ontology/sample_*.ttl` files and `ontology/demo_abox.ttl` explicitly.
- [ ] Verify the six benchmark products against the agreed matrix and add
  regression tests for every standard and expected issue.
- [ ] Establish when a Pass is justified, including handling of missing data,
  certificates and any agreed Allergen-Free rules. Retest substitutions against
  all selected targets.
- [ ] Measure complete request and rendering times with the final graph and
  realistic workloads against the two-second target.
- [ ] Inspect all three workflows, including graph node interaction, in a
  browser; test the deployed app and record its URL and environment.
- [ ] Prepare the technical report and verify the submission links.
