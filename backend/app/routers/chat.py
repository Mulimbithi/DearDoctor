from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User, ChatSession, Message, Screening, RiskEvent, Consent
from app.security import require_role
from app.chatbot.scripts import SCRIPT, get_text, get_options
from app.chatbot.epds import EPDS_ITEMS, total_score
from app.chatbot.risk import (
    classify,
    open_case,
    counsellor_line,
    current_referral,
    notify_assigned_consultant,
)
from app.chatbot.results import build_result
from app.chatbot.crisis import detect_crisis

router = APIRouter(prefix="/api/chat", tags=["chat"])

def own_session(db: Session, session_id: int, token: dict) -> ChatSession:
    session = db.get(ChatSession, session_id)
    if not session or session.user_id != int(token["sub"]):
        raise HTTPException(status_code=404, detail="Session not found")
    return  session
def save_msg(db: Session, session_id: int, sender: str, text: str):
    db.add(Message(session_id=session_id, sender=sender, text=text))

def node_payload(node: str, lang: str, name: str= ""):
    return {"type": "node", "node": node,
            "text": get_text(node, lang, name),
            "options": get_options(node, lang)}
def epds_question(item_no: int):
    item = EPDS_ITEMS[item_no - 1]
    return {"type": "epds", "item": item_no, "text": item["question"],
            "options": [{"id": i, "label": label}
                        for i, label in enumerate(item["options"])]}
def declined_here(db: Session, session_id: int) -> bool:
    return db.query(Message).filter(Message.session_id == session_id,
                                    Message.text == "consent:decline").first() is not None
def has_agreed(db, user_id):
    # agreed inside a chat earlier?
    in_chat = (db.query(Message)
                 .join(ChatSession, Message.session_id == ChatSession.id)
                 .filter(ChatSession.user_id == user_id,
                         Message.text == "consent:agree")
                 .first()) is not None
    if in_chat:
        return True
    # or agreed when she registered?
    at_signup = (db.query(Consent)
                   .filter(Consent.user_id == user_id,
                           Consent.consent_given == True)
                   .first()) is not None
    return at_signup

@router.post("/start")
def start_chat(lang: str = "en",
               token=Depends(require_role("mother")),
               db: Session = Depends(get_db)):
    user = db.get(User, int(token["sub"]))
    if not user or user.status != "active":
        raise HTTPException(status_code=404, detail="User not found")
    returning = (db.query(ChatSession)
                 .filter(ChatSession.user_id == user.id).count()) > 0
    node = "welcome_back" if returning else "welcome_new"

    session= ChatSession(user_id=user.id)
    db.add(session)
    db.commit()

    payload = node_payload(node, lang, user.pseudonym or "friend")
    payload["session_id"] = session.id
    payload["returning"] = returning
    return payload

class ChooseIn(BaseModel):
    session_id:int
    node: str
    choice: str
    lang: str = "en"


@router.post("/choose")
def choose(data: ChooseIn,
           token=Depends(require_role("mother")),
           db: Session =  Depends(get_db)):
    session = own_session(db, data.session_id, token)
    user = db.get(User, session.user_id)

    node = SCRIPT.get(data.node)
    if not node or data.choice not in node["next"]:
        raise HTTPException(status_code=400, detail="Unknown node or choice")
    target = node["next"][data.choice]

    if data.node == "consent":
        save_msg(db, session.id, "mother", f"consent:{data.choice}")

    notification_referral = None
    #mother asked to speak to a counsellor after a low or moderate risk result
    if data.choice == "yes" and data.node.startswith(("result_low", "result_moderate")):
        screening = (db.query(Screening)
                     .filter(Screening.session_id == session.id)
                     .order_by(Screening.id.desc()).first())
        if not screening:
            raise HTTPException(status_code=400, detail="No screening in this session")
        already = (db.query(RiskEvent)
                   .filter(RiskEvent.screening_id == screening.id,
                           RiskEvent.trigger == "requested_by_mother").first())
        if not already:
            referral, created = open_case(
                db, user.id, screening.id, classify(screening.answers),
                "requested_by_mother",
            )
            if created:
                notification_referral = referral
    db.commit()
    if notification_referral:
        notify_assigned_consultant(db, notification_referral)

    if target == "EPDS":
        return epds_question(1)
    payload = node_payload(target, data.lang, user.pseudonym or "friend")
    if target == "consultant_requested":
        payload["text"] += counsellor_line(db, current_referral(db, user.id))
    return payload

class EpdsAnswerIn(BaseModel):
    session_id: int
    item: int
    option: int
    lang: str = "en"

@router.post("/epds")
def epds_answer(data: EpdsAnswerIn,
                token=Depends(require_role("mother")),
                db: Session = Depends(get_db)):
    session = own_session(db, data.session_id, token)
    user = db.get(User, session.user_id)

    if declined_here(db, session.id):
        raise HTTPException(status_code=403, detail="Consent was declined")
    if not has_agreed(db, user.id):
        raise HTTPException(status_code=403, detail="Consent is needed first")
    if data.item not in range(1, 11) or data.option not in (0, 1, 2, 3):
        raise HTTPException(status_code=400, detail="Invalid answer")
    save_msg(db, session.id, "mother", f"epds:{data.item}:{data.option}")
    db.commit()

    if data.item < 10:
        return epds_question(data.item + 1)

    # runs after the mother answers question 10 and scores her answers, saves results and decides what's next
    rows = (db.query(Message)
            .filter(Message.session_id == session.id,
                    Message.text.like("epds:%"))# asks for all messages in this session whose text starts with epds %means anything can follow after the epds label
            .order_by(Message.id).all())#puts them in the order they were saved from q1 to 10 and returns the whole list(.all())
    latest = {}
    for m in rows:
        _, item, option = m.text.split(":")
        latest[int(item)] = int(option)
    if len(latest) != 10:#checks whether all questions were answered
        raise HTTPException(status_code=400, detail="Please answer  all 10 questions")
    answers = [latest[i] for i in range(1, 11)]

    previous = (db.query(Screening).filter(Screening.user_id == user.id)
                .order_by(Screening.id.desc()).first())#checks in descending order(desc)for precvious results if she had any
    previous_total = previous.total_score if previous else None#for the comparison message to check for improvement

    total = total_score(answers)#adds up the points
    level = classify(answers)#turns answers into low moderate or high risk etc

    screening = Screening(user_id=user.id, session_id=session.id, answers=answers,
                          total_score=total, item10_value=answers[9])
    db.add(screening)
    db.flush()# sends the new row to the database without finishing the save so it can be used in open_case

    notification_referral = None
    if level in("high", "urgent"):
        trigger = "item10_positive" if level == "urgent" else "epds_high"
        referral, created = open_case(db, user.id, screening.id, level, trigger)
        if created:
            notification_referral = referral
    db.commit()#save screening and any case/referral created for a high-risk result
    if notification_referral:
        notify_assigned_consultant(db, notification_referral)

    node, text = build_result(level, previous_total, total, data.lang,
                              user.pseudonym or "friend")
    if level in ("high", "urgent"):
        text = text + counsellor_line(db, current_referral(db, user.id))
    payload = node_payload(node, data.lang, user.pseudonym or "friend")
    payload["text"] = text
    return payload

class MessageIn(BaseModel):
    session_id: int
    text: str
    lang: str = "en"

@router.post("/message")
def typed_message(data: MessageIn,
                  token=Depends(require_role("mother")),
                  db: Session = Depends(get_db)):
    session = own_session(db, data.session_id, token)
    user = db.get(User, session.user_id)
    name = user.pseudonym or "friend"
    declined = declined_here(db, session.id)

    category = detect_crisis(data.text)
    if category:
        if not declined:
            save_msg(db, session.id, "system", f"urgent:{category}")
            db.commit()
            referral, created = open_case(db, user.id, None, "urgent", category)
            db.commit()
            if created:
                notify_assigned_consultant(db, referral)
        return node_payload("crisis", data.lang, name)

    if not declined:
        save_msg(db, session.id, "mother", data.text)
        db.commit()
    return node_payload("fallback", data.lang, name)
