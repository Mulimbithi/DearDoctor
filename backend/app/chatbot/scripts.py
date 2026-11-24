HELPLINES = {
    "en": "Child Helpline 116 or LVCT Health 1190",

}
SCRIPT = {
    "welcome_new": {
        "text": {
            "en": "Hello, {name}. My name is docBot. I'm an automated assistant "
                  "here to listen and check how you've been feeling. I am not a "
                  "doctor.",
        },
        "options":[
            {"id": "start", "label": {"en": "Let's begin"}},
            {"id": "info", "label": {"en": "Tell me more"}},
        ],
        "next": {"start": "consent", "info": "about"},
    },
    "welcome_back": {
        "text": {
            "en": "Welcome back, {name}. It's good to see you again. Would you "
                  "like to check in on how you have been feeling?",
        },
        "options":[
            {"id": "checkin", "label": {"en": "Yes, check in"}},
            {"id": "later", "label": {"en": "Not now", }},
        ],
        "next": {"checkin": "epds_intro", "later": "goodbye"},
    },
    "goodbye": {
        "text":{
            "en": "Take care, {name}. You can come back any time. If you need"
                   " help, call " + HELPLINES["en"] + ".",
        },
        "options": [],
        "next": {},
    },

    "about": {
        "text": {
            "en": "I will ask 10 short questions about the last 7 days. If your "
                  "answers show you may need support, a counsellor from our team "
                  "can follow up with you. You can stop at any time.",
        },
        "options": [
            {"id": "continue", "label": {"en": "Continue",}},
        ],
        "next": {"continue": "consent"},
    },

    "consent": {
        "text": {
            "en": "Before we start: your answers are saved so a counsellor can "
                  "help you if you need it. We keep your number only to let you "
                  "sign in and if you choose, to allow consultants to contact you. "
                  "Do you agree to continue?",

        },
        "options": [
            {"id": "agree", "label": {"en": "I agree", }},
            {"id": "decline", "label": {"en": "I do not agree"}},
        ],
        "next": {"agree": "epds_intro", "decline": "consent_declined"},
    },
    "consent_declined": {
        "text": {
            "en": "That's okay. Your answers from this chat will not be saved. "
                  "If you need to talk to someone, you can call "
                  + HELPLINES["en"] + ".",
        },
        "options": [],
        "next": {},
    },
    "epds_intro": {
        "text": {
            "en": "Alright, let's get started! For each question, choose the answer that comes "
                  "closest to how you have felt in the past 7 days.",
        },
        "options": [
            {"id": "ok", "label":  {"en": "Start", }},
        ],
        "next": {"ok": "EPDS"},
    },
    "result_high": {
        "text": {
            "en": "That's all of the questions. Thank you for being honest with me. "
                  "It sounds like things have been hard lately, and noticing that is "
                  "the first and most important step. You don't have to go through "
                  "this on your own. One of our counsellors will reach out to you "
                  "soon. You can also call " + HELPLINES["en"] + " any time.",
        },
        "options": [],
        "next": {},
    },
    "result_high_repeat": {
        "text": {
            "en": "Thank you for checking in again, {name}, and for being honest "
                  "with me. It sounds like things are still hard right now. A "
                  "counsellor from our team will reach out to you soon. You can "
                  "also call " + HELPLINES["en"] + " any time.",
        },
        "options": [],
        "next": {},
    },
    "result_urgent": {
        "text": {
            "en": "Thank you for telling me. What you shared is important, and "
                  "I'm glad you told me. It is okay to not be doing well, and it is "
                  "important that you get support as soon as possible. Please go to "
                  "your nearest hospital or ask someone you trust to stay with you. "
                  "A counsellor from our team has been told and will be in touch "
                  "soon. If you are in danger right now, call " + HELPLINES["en"] + ".",
        },
        "options": [],
        "next": {},
    },
    "result_urgent_repeat": {
        "text": {
            "en": "Thank you for checking in again, {name}. What you shared "
                  "is important, and I'm glad you told me. It is okay to not "
                  "be doing well, and it is important that you get support as "
                  "soon as possible. Please go to your nearest hospital or ask "
                  "someone you trust to stay with you. A counsellor from our "
                  "team has been told and will be in touch soon. If you are in "
                  "danger right now, call " + HELPLINES["en"] + ".",
        },
        "options": [],
        "next": {},
    },
    "crisis": {
        "text": {
            "en": "I'm really sorry you feel this way. You matter, and help is "
                  "available right now. Please call " + HELPLINES["en"] +
                  ", or go to the nearest hospital or health centre. If you can, "
                  "ask someone you trust to stay with you.",
        },
        "options": [],
        "next": {},
    },
    "fallback": {
        "text": {
            "en": "Sorry, I didn't understand that. Please choose one of the "
                  "options shown. If you need help right now, call "
                  + HELPLINES["en"] + ".",
        },
        "options": [],
        "next": {},
    },
     "result_low": {
        "text": {
            "en": "Thank you for answering. Your answers don't suggest you need "
                  "urgent support right now. If you would like to talk to a "
                  "counsellor anyway, we can arrange that. Would you like one to "
                  "contact you?",
            "sw": "",
        },
        "options": [
            {"id": "yes", "label": {"en": "Yes, please", "sw": ""}},
            {"id": "no", "label": {"en": "Not now", "sw": ""}},
        ],
        "next": {"yes": "consultant_requested", "no": "consultant_not_now"},
    },

    "result_low_repeat": {
        "text": {
            "en": "Thank you for checking in again, {name}. Your answers don't "
                  "suggest you need urgent support right now. Would you like a "
                  "counsellor to contact you?",
            "sw": "",
        },
        "options": [
            {"id": "yes", "label": {"en": "Yes, please", "sw": ""}},
            {"id": "no", "label": {"en": "Not now", "sw": ""}},
        ],
        "next": {"yes": "consultant_requested", "no": "consultant_not_now"},
    },

    "result_moderate": {
        "text": {
            "en": "Thank you for answering. It sounds like you may be going "
                  "through a hard time, and talking to a counsellor can help. "
                  "Would you like one to contact you?",
            "sw": "",
        },
        "options": [
            {"id": "yes", "label": {"en": "Yes, please", "sw": ""}},
            {"id": "no", "label": {"en": "Not now", "sw": ""}},
        ],
        "next": {"yes": "consultant_requested", "no": "consultant_not_now"},
    },

    "result_moderate_repeat": {
        "text": {
            "en": "Thank you for checking in again, {name}. It sounds like "
                  "things may still be hard. Would you like a counsellor to "
                  "contact you?",
            "sw": "",
        },
        "options": [
            {"id": "yes", "label": {"en": "Yes, please", "sw": ""}},
            {"id": "no", "label": {"en": "Not now", "sw": ""}},
        ],
        "next": {"yes": "consultant_requested", "no": "consultant_not_now"},
    },

    "consultant_requested": {
        "text": {
            "en": "Thank you. A counsellor from our team will contact you. You "
                  "can also call " + HELPLINES["en"] + " any time.",
            "sw": "",
        },
        "options": [],
        "next": {},
    },

    "consultant_not_now": {
        "text": {
            "en": "That's okay. You can come back any time, and if you change "
                  "your mind you can ask for a counsellor then. You can also "
                  "call " + HELPLINES["en"] + " any time.",
            "sw": "",
        },
        "options": [],
        "next": {},
    },
    
}
def get_text(node_id: str, lang: str = "en", name: str = "") -> str:
    text = SCRIPT[node_id]["text"]
    chosen = text.get(lang) or text["en"]
    return chosen.replace("{name}", name or "friend")
def get_options(node_id: str, lang: str = "en") -> list:
    return[
        {"id": o["id"], "label": o["label"].get(lang) or o["label"]["en"]}
        for o in SCRIPT[node_id]["options"]
    ]