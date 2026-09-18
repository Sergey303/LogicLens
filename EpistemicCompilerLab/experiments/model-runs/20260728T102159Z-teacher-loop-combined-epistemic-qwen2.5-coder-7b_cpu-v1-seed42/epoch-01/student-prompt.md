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

- Before using the representation, extract the date and revision explicitly stated in the user question.
- If either required field is absent, immediately return `action=ask_user`, `status=need_user`, `material=null`, and set `askField` to the absent field. Do not infer a missing field from the representation or choose a material.
- Use `need_user` only with `action=ask_user` and a non-null `askField`.
- Use `success` only when the supplied representation determines one material.
- Use `unknown` when the representation does not support the requested revision or cannot determine the answer.
- Never rewrite `unknown` as `false` and never invent a default.
- Preserve material identifiers exactly as lowercase `asd2` or `asd100500`.
- Do not reveal hidden reasoning. Keep `answerRu` concise.
