def _normalize_confirmation(confirmation_status: str) -> float:
    value = (confirmation_status or "").strip().lower()
    confirmed_values = {"confirmed", "confirm", "yes", "true", "1", "accepted"}
    return 1.0 if value in confirmed_values else 0.0


def _normalize_duration(call_duration: float) -> float:
    bounded = max(0.0, min(float(call_duration), 300.0))
    return bounded / 300.0


def _invert_hesitation(hesitation_score: float) -> float:
    bounded = max(0.0, min(float(hesitation_score), 1.0))
    return 1.0 - bounded


def calculate_interaction_score(
    confirmation_status: str,
    call_duration: float,
    hesitation_score: float,
) -> float:
    confirmation = _normalize_confirmation(confirmation_status)
    duration = _normalize_duration(call_duration)
    confidence = _invert_hesitation(hesitation_score)

    # Weighted contextual scoring over one interaction only.
    score_0_1 = (0.5 * confirmation) + (0.3 * duration) + (0.2 * confidence)
    return round(score_0_1 * 100.0, 2)

