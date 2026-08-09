PROGRAM_VERSION = "0.1.0"


def strict_status(positive_evidence, negative_evidence):
    if not isinstance(positive_evidence, bool) or not isinstance(negative_evidence, bool):
        raise ValueError("invalid_arguments")
    if positive_evidence and negative_evidence:
        return {"status": "conflicting", "value": None}
    if positive_evidence:
        return {"status": "supported", "value": True}
    if negative_evidence:
        return {"status": "refuted", "value": False}
    return {"status": "unknown", "value": None}


def threshold_relation(value, threshold):
    if isinstance(value, bool) or isinstance(threshold, bool):
        raise ValueError("invalid_arguments")
    if not isinstance(value, (int, float)) or not isinstance(threshold, (int, float)):
        raise ValueError("invalid_arguments")
    if value > threshold:
        relation = "above"
    elif value < threshold:
        relation = "below"
    else:
        relation = "equal"
    return {"status": "ok", "value": relation}


def interval_threshold(lower, upper, threshold):
    values = (lower, upper, threshold)
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) for v in values):
        raise ValueError("invalid_arguments")
    if lower > upper:
        raise ValueError("invalid_arguments")
    if lower > threshold:
        return {"status": "supported", "value": "above"}
    if upper < threshold:
        return {"status": "refuted", "value": "above"}
    return {"status": "unknown", "value": None}
