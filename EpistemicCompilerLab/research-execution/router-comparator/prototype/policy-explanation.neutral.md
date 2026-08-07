# Frozen teacher routing explanation — synthetic TRAIN/DEV prototype

This policy chooses among declared read-only capabilities. It never decides whether a claim is true, false, supported, refuted, unknown, or conflicting.

1. Reject state-changing requests.
2. Claim-resolution requests require both scope and version.
3. If a claim-resolution request explicitly requires the strict policy contract, use the policy resolver; otherwise use the ordinary claim resolver.
4. Provenance lookup requires scope and version.
5. Numeric threshold checks use the deterministic threshold capability.
6. Explanation requests use the result explainer only after a structured result already exists.
7. If no declared goal matches, ask for clarification.

Capability handles and visible labels come from the frozen capability registry. The policy itself references only internal canonical capability IDs. Qwen-visible labels/descriptions are a separate DEV-only treatment factor and may not change the routing policy.
