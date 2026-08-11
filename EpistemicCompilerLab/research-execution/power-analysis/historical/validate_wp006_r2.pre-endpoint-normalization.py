# Historical snapshot marker for the pre-R3 validator.
# Exact pre-normalization implementation remains recoverable from candidate
# 8d7393ff43ba4ea2c153438ff880903609a355d5 at
# EpistemicCompilerLab/research-execution/power-analysis/prototype/validate_wp006_r2.py.
#
# It required primary_estimand.outcome == publication_composite_correctness and
# is intentionally not executable as the current acceptance authority after
# ENDPOINT_IDENTITY_CONTRACT.json normalized the primary ID to
# scenario_level_exact_epistemic_contract_accuracy.

HISTORICAL_CANDIDATE_SHA = "8d7393ff43ba4ea2c153438ff880903609a355d5"
HISTORICAL_PATH = "EpistemicCompilerLab/research-execution/power-analysis/prototype/validate_wp006_r2.py"
HISTORICAL_PRIMARY_ENDPOINT_ASSERTION = "publication_composite_correctness"
STATUS = "SUPERSEDED_BY_R3_ENDPOINT_IDENTITY_NORMALIZATION"
