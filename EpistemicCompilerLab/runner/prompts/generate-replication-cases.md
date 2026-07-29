# Frozen replication case generator

Generate exactly 24 new Russian questions for a material-selection system. You do not receive parser code or existing benchmark wording. Return only the supplied JSON schema.

Create exactly six cases of each `caseKind`:

- `success`: Latin revision A with any listed date, or Latin revision B with a listed date;
- `unknown`: Latin revision C with a listed date;
- `missing_date`: Latin revision A or B is explicit, but no calendar date appears;
- `missing_revision`: a listed date is explicit, but no revision or version letter appears.

Annotation rules:

- `revision` and `date` must describe the literal question accurately;
- use Latin letters `A`, `B`, `C`, never Cyrillic lookalikes;
- use `revision="missing"` only for `missing_revision`;
- use `date=0` and `dateStyle="none"` only for `missing_date`;
- among the 18 dated cases create exactly six `words`, six `dotted` and six `iso` cases;
- use only dates 30 June 2026, 1 July 2026 and 10 August 2026;
- never mention material identifiers or expected answers;
- use unique IDs beginning with `rep-` and unique questions;
- vary syntax, word order and vocabulary naturally;
- set `hasDistractor=true` for exactly 12 cases and add one harmless phrase about a board, installation, inspection, batch or documentation, without adding another date or revision;
- do not include benchmark terminology, split names, scorer fields or explanations.

The questions must remain unambiguous to a Russian-speaking reviewer. Do not reveal hidden reasoning.
