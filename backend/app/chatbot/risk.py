from app.chatbot.epds import total_score, item10_positive, HIGH_RISK_THRESHOLD


def classify(answers: list) -> str:
    """Returns 'urgent', 'high' or 'none'."""
    if item10_positive(answers):
        return "urgent"
    if total_score(answers) >= HIGH_RISK_THRESHOLD:
        return "high"
    return "none"