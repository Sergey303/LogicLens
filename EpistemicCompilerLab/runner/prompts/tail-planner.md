# Optional-tail planner contract

Decide whether the user question needs one optional knowledge tail after the base CLI result is known.

Available tail kinds:

- `evidence` — source or audit material explaining a rule;
- `exceptions` — the explicit exception set for a default rule.

Return exactly one JSON object and no surrounding prose or Markdown.

Schema:

```json
{
  "openTail": true,
  "entity": "entity identifier or null",
  "kind": "evidence | exceptions | null"
}
```

Rules:

- Open no tail for a direct material-selection question when the compact result and proof already answer it.
- Open `evidence` for an explicit why, source, proof or audit request.
- Open `exceptions` for an explicit request to inspect exceptions to a rule.
- Set `openTail=false`, `entity=null`, and `kind=null` when no tail is necessary.
- Select the entity that owns the requested tail; it is not necessarily the final material in every future benchmark.
- Do not open a tail merely because one is available.
- Do not reveal hidden reasoning.
