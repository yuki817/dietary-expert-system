# Validation and remaining acceptance work

The application loads the supplied ontology and six-product benchmark dataset.
The dietary rules are provisional and `Not assessed` is not a Pass. Do not use
the results as an actual compliance determination.

## Checks available now

Run `python -m unittest discover -s tests -v` in the project virtual
environment. This checks graph loading and traversal, selected inference rules,
session-local recipes, role matching and simulation, plus Streamlit sample
workflows. Streamlit's application testing exercises the server-side UI; it
does not verify the interactive graph component visually in a browser.

Previous timing measurements used the smaller sample graph; performance on the
supplied dataset and end-to-end UI rendering remain to be measured.

## Before final acceptance

- [ ] Resolve the policy questions in `TEAM_DISCUSSION.md` and update the
  specification, rules, ontology, and expected results together.
- [ ] Confirm the supplied T-Box and A-Box represent the team's agreed final data.
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
