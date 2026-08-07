from __future__ import annotations
import copy
from typing import Any

from decision_graph import load_feature_contract, validate_features


def normalize_precomputed_features(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate and copy an independently supplied typed feature vector.

    This adapter deliberately does not inspect raw natural-language questions.
    Raw-question feature extraction is a separate DEV-only treatment.
    """
    contract = load_feature_contract()
    features = copy.deepcopy(payload)
    validate_features(features, contract)
    return features
