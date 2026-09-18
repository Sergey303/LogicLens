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

- Before consulting the representation, verify that the user question explicitly supplies both a date and a revision.
- If the date is absent, return `action=ask_user`, `status=need_user`, `material=null`, and `askField=date`; do not infer a date from the representation or the current date.
- If the revision is absent, return `action=ask_user`, `status=need_user`, `material=null`, and `askField=revision`; do not select or infer a revision.
- Use `need_user` only with `action=ask_user` and a non-null `askField`.
- Use `success` only when the supplied representation determines one material.
- Use `unknown` when the representation does not support the requested revision or cannot determine the answer.
- Never rewrite `unknown` as `false` and never invent a default.
- Preserve material identifiers exactly as lowercase `asd2` or `asd100500`.
- Do not reveal hidden reasoning. Keep `answerRu` concise.
