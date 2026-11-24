REVERSE_ITEMS = {3, 5, 6, 7, 8, 9, 10}   # these are scored 3,2,1,0 down the page
# Edinburgh Postnatal Depression Scale (EPDS)
# Source: Cox, J.L., Holden, J.M., and Sagovsky, R. 1987. Detection of postnatal
# depression: Development of the 10-item Edinburgh Postnatal Depression Scale.
# British Journal of Psychiatry 150:782-786.
# Options are listed top to bottom, exactly as on the official form.
EPDS_ITEMS = [
    {"question": "I have been able to laugh and see the funny side of things",
     "options": ["As much as I always could", "Not quite so much now",
                 "Definitely not so much now", "Not at all"]},

    {"question": "I have looked forward with enjoyment to things",
     "options": ["As much as I ever did", "Rather less than I used to",
                 "Definitely less than I used to", "Hardly at all"]},

    {"question": "I have blamed myself unnecessarily when things went wrong",
     "options": ["Yes, most of the time", "Yes, some of the time",
                 "Not very often", "No, never"]},

    {"question": "I have been anxious or worried for no good reason",
     "options": ["No, not at all", "Hardly ever",
                 "Yes, sometimes", "Yes, very often"]},

    {"question": "I have felt scared or panicky for no very good reason",
     "options": ["Yes, quite a lot", "Yes, sometimes",
                 "No, not much", "No, not at all"]},

    {"question": "Things have been getting on top of me",
     "options": ["Yes, most of the time I haven't been able to cope at all",
                 "Yes, sometimes I haven't been coping as well as usual",
                 "No, most of the time I have coped quite well",
                 "No, I have been coping as well as ever"]},

    {"question": "I have been so unhappy that I have had difficulty sleeping",
     "options": ["Yes, most of the time", "Yes, sometimes",
                 "Not very often", "No, not at all"]},

    {"question": "I have felt sad or miserable",
     "options": ["Yes, most of the time", "Yes, quite often",
                 "Not very often", "No, not at all"]},

    {"question": "I have been so unhappy that I have been crying",
     "options": ["Yes, most of the time", "Yes, quite often",
                 "Only occasionally", "No, never"]},

    {"question": "The thought of harming myself has occurred to me",
     "options": ["Yes, quite often", "Sometimes",
                 "Hardly ever", "Never"]},
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