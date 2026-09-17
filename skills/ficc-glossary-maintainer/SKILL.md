---
name: ficc-glossary-maintainer
description: Add consistent plain-language FICC glossary entries with a public source and the project day on which each term was introduced.
license: MIT
covers:
  - docs/learning/ficc-glossary.md
last_verified_commit: e9e1dae
---

# ficc-glossary-maintainer

Use this skill whenever a fixed income, currencies, or commodities term first
appears in code, tests, architecture, or learning notes.

## Which tier does the term belong in?

The glossary has two sections, and this is the first decision to make.

**Ask: does the term carry something specific to *this* repository's code,
fixtures, or agent output that a dictionary definition would miss?**

- **Yes** → a full entry under `## Terms with repository-specific meaning`.
  Callable bond qualifies because the entry documents a real gap in
  `src/ingestion/fixed_income.py`'s validator; basis point qualifies because
  it explains the scenario tool's `shock_bps` argument.
- **No** → a one-line entry under `## General vocabulary`, linking to
  pm-mechanics. General PM/FICC vocabulary is that repository's
  responsibility; defining it fully in both places lets the two drift.

## Entry format — repository-specific terms

Keep entries alphabetical and use this exact shape:

```markdown
## Term

**Plain-language definition:** One short paragraph that explains the term
without assuming specialist knowledge.

**Introduced:** Day N

**Public source:** [Descriptive source name](https://public.example/source)
```

## Entry format — general vocabulary

A heading, one sentence, and a link. The heading stays a heading rather than
becoming a bullet: quiz banks cite `#anchor` fragments into this file, and
anchors derive from heading text, so removing the heading breaks the
citation silently.

```markdown
### Term

One sentence of orientation. [Derive it →](https://navoditk.github.io/pm-mechanics/reference/<section>/<page>/)
```

Verify the link resolves before committing — a dead link here is worse than
no link, because the reader has already been told not to expect the
definition locally.

## Rules

- Define the term in the context in which this project uses it.
- Expand abbreviations on first use and avoid defining one unknown term with
  several others.
- Prefer primary public sources such as central banks and regulators; use a
  reputable educational source when it explains the concept more clearly.
- Link to a specific source page, not a search result or generic home page.
- Do not include proprietary examples, company-sensitive information, or
  investment recommendations.
- Update an existing entry instead of adding a duplicate or near-synonym.
