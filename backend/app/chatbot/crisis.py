import re

# STARTER LISTS. They must be reviewed and extended by your clinical advisor
# and a Swahili speaker before real use. Write phrases in lower case.
# Apostrophes are removed when matching, so write "dont", "cant", "im".

SELF_HARM_EN = [
    "kill myself", "kill my self", "want to die", "wanna die", "wana die",
    "end my life", "end it all", "take my own life", "suicide", "suicidal",
    "dont want to live", "do not want to live", "better off dead",
    "hurt myself", "harm myself", "no reason to live", "cant go on",
    "dont want to be here anymore","I hate my life",
]

HARM_BABY_EN = [
    "hurt my baby", "harm my baby", "kill my baby", "hurt the baby",
    "harm the baby", "i might hurt my child",
]

SELF_HARM_SW = [
    "nataka kufa", "ningependa kufa", "nataka kujiua", "nitajiua",
    "sitaki kuishi", "sioni sababu ya kuishi", "nimechoka na maisha",
    "maisha hayana maana", "ni bora nife", "nataka kujidhuru",
    "nitajidhuru", "kujitoa uhai",
]

HARM_BABY_SW = [
    "nitamuumiza mtoto wangu", "nitamdhuru mtoto wangu",
    "nataka kumuumiza mtoto wangu", "nataka kumdhuru mtoto wangu",
]


def normalise(text: str) -> str:
    text = text.lower()
    text = text.replace("'", "").replace("\u2019", "")   # dont, cant, im
    text = re.sub(r"[^a-z0-9\s]", " ", text)             # drop punctuation
    return re.sub(r"\s+", " ", text).strip()


PHRASES = {
    "self_harm": [normalise(p) for p in SELF_HARM_EN + SELF_HARM_SW],
    "harm_baby": [normalise(p) for p in HARM_BABY_EN + HARM_BABY_SW],
}


def detect_crisis(text: str):
    """Returns 'self_harm', 'harm_baby' or None."""
    cleaned = " " + normalise(text) + " "
    for category, phrases in PHRASES.items():
        for phrase in phrases:
            if f" {phrase} " in cleaned:
                return category
    return None