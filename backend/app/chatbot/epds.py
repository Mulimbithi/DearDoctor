 # EPDS (Edinburgh Postnatal Depression Scale), 10 items.
# Each item has 4 options. Paste the OFFICIAL wording below, with the options
# in the same order as on the printed form (top to bottom).

REVERSE_ITEMS = {3, 5, 6, 7, 8, 9, 10}   # these are scored 3,2,1,0 down the page

EPDS_ITEMS = [
    {
        "id": n,
        "question": f"PASTE OFFICIAL WORDING OF ITEM {n}",
        "options": ["PASTE OPTION 1", "PASTE OPTION 2",
                    "PASTE OPTION 3", "PASTE OPTION 4"],
    }
    for n in range(1, 11)
]

# Set both with your clinical advisor.
MODERATE_THRESHOLD = 10
HIGH_RISK_THRESHOLD = 13


def score_answer(item_id: int, option_index: int) -> int:
    """option_index is 0-3: the position of the chosen option as printed."""
    if option_index not in (0, 1, 2, 3):
        raise ValueError("option_index must be 0, 1, 2 or 3")
    return 3 - option_index if item_id in REVERSE_ITEMS else option_index


def total_score(answers: list) -> int:
    """answers = the chosen option position (0-3) for each of the 10 items."""
    if len(answers) != 10:
        raise ValueError("EPDS needs exactly 10 answers")
    return sum(score_answer(i + 1, a) for i, a in enumerate(answers))


def item10_positive(answers: list) -> bool:
    """Item 10 is the self-harm item. Any score above 0 counts as positive."""
    return score_answer(10, answers[9]) > 0