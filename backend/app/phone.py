import re


def normalise_phone(raw: str) -> str:
    digits = re.sub(r"[^\d+]", "", raw)
    if digits.startswith("+254"):
        num = digits[1:]
    elif digits.startswith("254"):
        num = digits
    elif digits.startswith("0"):
        num = "254" + digits[1:]
    else:
        num = "254" + digits
    if not re.fullmatch(r"254[17]\d{8}", num):
        raise ValueError("Enter a valid Kenyan phone number")
    return "+" + num