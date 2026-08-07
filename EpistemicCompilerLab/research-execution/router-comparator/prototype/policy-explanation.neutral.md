# Frozen teacher routing explanation — synthetic TRAIN/DEV prototype

This policy chooses among declared read-only capabilities. It never decides whether a claim is true, false, supported, refuted, unknown, or conflicting.

The routing input is an independently supplied typed feature vector. For the primary comparison, M19, M20, and direct Qwen selection receive the same frozen feature values. Raw-question parsing is evaluated only in a separate DEV-only ablation.

1. Reject state-changing requests.
2. Claim-resolution requests require both scope and version.
3. If a claim-resolution request explicitly requires strict four-state epistemic handling, conflict preservation, or an auditable policy trace, select the strict-policy resolver; otherwise select the ordinary claim resolver.
4. Provenance lookup requires scope and version.
5. Numeric threshold checks use the deterministic threshold capability.
6. Explanation requests use the result explainer only after a structured result already exists.
7. If no declared goal matches, ask for clarification.

This policy selects a capability only. A separate held-equal binder supplies and validates capability arguments after routing.

Capability handles and visible labels come from the frozen capability registry. The policy itself references only internal canonical capability IDs. Qwen-visible labels/descriptions are a separate DEV-only treatment factor and may not change the routing policy, typed I/O schemas, budgets, or failure semantics.
