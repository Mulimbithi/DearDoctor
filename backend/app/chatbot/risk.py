from app.chatbot.epds import (total_score, item10_positive,
                              MODERATE_THRESHOLD, HIGH_RISK_THRESHOLD)


def classify(answers: list) -> str:
    """Returns 'urgent', 'high', 'moderate' or 'low'."""
    if item10_positive(answers):
        return "urgent"
    total = total_score(answers)
    if total >= HIGH_RISK_THRESHOLD:
        return "high"
    if total >= MODERATE_THRESHOLD:
        return "moderate"
    return "low"


def assigns_immediately(level: str) -> bool:
    return level in ("high", "urgent")


def offers_consultant(level: str) -> bool:
    return level in ("low", "moderate")