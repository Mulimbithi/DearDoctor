from app.chatbot.scripts import get_text

TREND_TEXT = {
    "lower": "Compared with your last check-in, your answers suggest you may be "
             "feeling a little better.",
    "same": "Compared with your last check-in, your answers are about the same.",
    "higher": "Compared with your last check-in, things seem to have become "
              "harder.",
}

# Ask your clinical advisor what counts as a meaningful change in score.
TREND_STEP = 3


def trend(previous_total, new_total):
    if previous_total is None:
        return None
    diff = new_total - previous_total
    if diff <= -TREND_STEP:
        return "lower"
    if diff >= TREND_STEP:
        return "higher"
    return "same"


def build_result(level: str, previous_total, new_total: int,
                 lang: str = "en", name: str = ""):
    """Picks the right message. previous_total is None on a first screening."""
    node = f"result_{level}" + ("_repeat" if previous_total is not None else "")
    text = get_text(node, lang, name)
    t = trend(previous_total, new_total)
    if t and level != "urgent":      # no comparison in an urgent message
        text = text + " " + TREND_TEXT[t]
    return node, text