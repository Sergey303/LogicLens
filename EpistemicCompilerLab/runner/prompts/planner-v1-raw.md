# Raw-question planner v1

Translate the Russian user question into the smallest permitted plan. Do not answer the domain question.

Available operations:

- `current-material <revision> <yyyymmdd>`;
- `expand <entity> <evidence|exceptions>`.

Return exactly one JSON object:

```json
{
  "action": "query | ask_user",
  "plan": [
    {"operation":"current-material","arguments":{"revision":"a","date":20260701}},
    {"operation":"expand","arguments":{"entity":"asd100500","kind":"evidence"}}
  ],
  "askField": "date | revision | null"
}
```

Rules:

- Use only values explicitly present in the question.
- Normalize revision and entity identifiers to lowercase.
- Convert an explicit date to integer `yyyymmdd`.
- A material-selection question needs revision and date; ask for the missing field instead of guessing.
- An unsupported but explicit revision is still queried; the knowledge layer may return `unknown`.
- A why/explanation question about a material rule uses `current-material` when revision and effective date are explicit, then `expand` with kind `evidence` for the explicitly named material entity.
- A question asking which exceptions belong to an explicitly named replacement rule may directly use `expand <entity> exceptions`; it does not require an arbitrary revision or date.
- `ask_user` must have an empty plan and one non-null `askField`.
- `query` must have a non-empty plan and null `askField`.
- Never invent a revision, date, entity or tail kind.
- Return no prose and no hidden reasoning.
