---
name: ficc-glossary-maintainer
description: Add consistent plain-language FICC glossary entries with a public source and the project day on which each term was introduced.
license: MIT
covers:
  - docs/ficc-glossary.md
last_verified_commit: 49bfd60
---

# ficc-glossary-maintainer

Use this skill whenever a fixed income, currencies, or commodities term first
appears in code, tests, architecture, or learning notes.

## Entry format

Keep entries alphabetical and use this exact shape:

```markdown
## Term

**Plain-language definition:** One short paragraph that explains the term
without assuming specialist knowledge.

**Introduced:** Day N

**Public source:** [Descriptive source name](https://public.example/source)
```

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
