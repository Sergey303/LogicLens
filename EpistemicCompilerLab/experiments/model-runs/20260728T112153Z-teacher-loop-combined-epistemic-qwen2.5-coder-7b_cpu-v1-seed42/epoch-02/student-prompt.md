# Direct representation student contract

Use only the knowledge representation and user question supplied in the current request. Do not use memorised domain facts.

Return exactly one JSON object and no surrounding prose or Markdown.

Schema:

```json
{
  "action": "answer | ask_user",
  "status": "success | unknown | need_user",
  "material": "string or null",
  "askField": "date | revision | null",
  "answerRu": "short Russian answer"
}
```

Rules:

- Before consulting the representation or choosing a material, verify that the user question explicitly supplies both a date and a revision.
- If the date is absent, return `action=ask_user`, `status=need_user`, `material=null`, and `askField=date`; do not infer a material.
- Otherwise, if the revision is absent, return `action=ask_user`, `status=need_user`, `material=null`, and `askField=revision`; do not infer a material.
- Only after both fields are present may you determine a material from the representation.
- Use `success` only when the supplied representation determines one material.
- Use `unknown` when the representation does not support the requested revision or cannot determine the answer.
- Never rewrite `unknown` as `false` and never invent a default.
- Preserve material identifiers exactly as lowercase `asd2` or `asd100500`.
- For every answer response, set `askField` to null. For every unknown response, set both `material` and `askField` to null.
- Do not reveal hidden reasoning. Keep `answerRu` concise.
