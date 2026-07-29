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
- for `words`, include exactly one of these literal substrings: `30 июня 2026`, `1 июля 2026`, `10 августа 2026`; the optional word `года` may follow;
- for `dotted`, include exactly one of: `30.06.2026`, `01.07.2026`, `10.08.2026`;
- for `iso`, include exactly one of: `2026-06-30`, `2026-07-01`, `2026-08-10`;
- do not spell day numbers as words, add ordinal suffixes, use slashes, shorten the year, or use relative dates;
- never mention material identifiers or expected answers;
- use unique IDs beginning with `rep-` and unique questions;
- vary syntax, word order and vocabulary naturally without changing the literal date form;
- set `hasDistractor=true` for exactly 12 cases and add one harmless phrase about a board, installation, inspection, batch or documentation, without adding another date or revision;
- do not include benchmark terminology, split names, scorer fields or explanations.

The questions must remain unambiguous to a Russian-speaking reviewer. Do not reveal hidden reasoning.
