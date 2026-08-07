# Frozen Qwen guide — relational comparator v0

Use only the typed catalogue. Never write SQL.

For a question about whether one declared proposition holds in a scope/version, call `resolve_claim` with the proposition identifier, scope identifier and version supplied by the experiment adapter. Do not invent identifiers and do not substitute another endpoint.

The returned row is authoritative for the relational comparator. Preserve `supported`, `refuted`, `unknown` and `conflicting` as distinct states. Preserve the returned action. Use evidence/provenance only to explain the result; do not repair, override or infer a different database result.

If a typed call cannot be formed from the visible inputs, emit the frozen query-formation failure object rather than free SQL or a guessed answer.
