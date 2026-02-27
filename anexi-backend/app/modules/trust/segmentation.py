HIGH_TRUST = "HIGH_TRUST"
STABLE = "STABLE"
RISK = "RISK"
HIGH_RISK = "HIGH_RISK"


def segment_from_score(interaction_score: float) -> str:
    score = float(interaction_score)
    if score >= 80:
        return HIGH_TRUST
    if score >= 60:
        return STABLE
    if score >= 40:
        return RISK
    return HIGH_RISK


def recommended_action_for_segment(segment: str) -> str:
    mapping = {
        HIGH_TRUST: "ship_priority",
        STABLE: "ship_normal",
        RISK: "double_check",
        HIGH_RISK: "manual_review",
    }
    return mapping.get(segment, "manual_review")

