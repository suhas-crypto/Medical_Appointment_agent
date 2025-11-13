from typing import Tuple
from ..rag.faq_rag import FAQRetriever
import requests, os, json
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
CAL_API = "http://localhost:8000/api/calendly"

def detect_intent(text: str):
    t = text.lower()
    if any(k in t for k in ["cancel", "cancelled", "call off", "drop"]):
        return "cancel"
    if any(k in t for k in ["resched", "reschedule", "change my", "move my"]):
        return "reschedule"
    if any(k in t for k in ["book", "appointment", "schedule", "need to book"]):
        return "schedule"
    if any(k in t for k in ["insurance","hours","parking","covid","policy","directions","documents","price","fees"]):
        return "faq"
    return "unknown"

class SchedulingAgent:
    def __init__(self):
        self.retriever = FAQRetriever()
        self.sessions = {}

    def _init_session(self, user_id):
        if user_id not in self.sessions:
            self.sessions[user_id] = {"stage":"greeting", "collected":{}}
        return self.sessions[user_id]

    def handle_message(self, user_id: str, message: str, context: dict) -> Tuple[str, dict]:
        session = self._init_session(user_id)
        intent = detect_intent(message)

        # If user explicitly asks FAQ, answer immediately
        if intent == "faq":
            answer = self.retriever.get_answer(message)
            return answer, session

        # If in the middle of booking flow, continue that
        if session.get("flow") == "reschedule":
            return self._handle_reschedule_flow(session, message)
        if session.get("flow") == "cancel":
            return self._handle_cancel_flow(session, message)
        if session.get("flow") == "schedule" or session["stage"] != "greeting":
            # continue scheduling flow
            return self._handle_schedule_flow(session, message)

        # Not in a flow yet - route based on intent
        if intent == "cancel":
            session["flow"] = "cancel"
            session["stage"] = "ask_cancel_info"
            return "Sure — I can help cancel an appointment. Could you provide your booking ID or the email used to book?", session
        if intent == "reschedule":
            session["flow"] = "reschedule"
            session["stage"] = "ask_booking_id"
            return "Okay — I can help reschedule. What's your booking ID (or email) for the appointment you'd like to move?", session
        if intent == "schedule":
            session["flow"] = "schedule"
            session["stage"] = "ask_reason"
            return "Hi — I'd be happy to help you schedule an appointment. What's the main reason for your visit today?", session

        # Unknown intent: ask clarifying question and offer FAQ or booking
        session["stage"] = "clarify"
        return "Do you want to (A) schedule a new appointment, (B) reschedule an existing one, (C) cancel, or (D) ask about clinic info (hours, insurance, etc.)? Please reply A/B/C/D.", session

    def _handle_schedule_flow(self, session, message):
        stage = session.get("stage","ask_reason")
        if stage == "ask_reason":
            session["collected"]["reason"] = message
            session["stage"] = "ask_type"
            return "Thanks. Which type of appointment would you prefer? (consultation|followup|physical|specialist)", session

        if stage == "ask_type":
            appt_type = message.lower()
            if appt_type not in ("consultation","followup","physical","specialist"):
                return "I didn't recognize that type. Please choose: consultation, followup, physical, or specialist.", session
            session["collected"]["appointment_type"] = appt_type
            session["stage"] = "ask_pref"
            return "Do you have a preferred date or 'anytime this week' / 'tomorrow' / 'morning' / 'afternoon'?", session

        if stage == "ask_pref":
            pref = message
            session["collected"]["preference"] = pref
            # query mock Calendly
            try:
                r = requests.get(f"{CAL_API}/availability", params={"appointment_type": session['collected']['appointment_type']}, timeout=3)
                avail = r.json()
                suggestions = []
                for d in avail.get('dates', []):
                    for s in d.get('available_slots', []):
                        suggestions.append({"date": d['date'], "start_time": s['start_time'], "end_time": s['end_time']})
                        if len(suggestions) >= 4:
                            break
                    if len(suggestions) >= 4:
                        break
                session['suggestions'] = suggestions
                session['stage'] = 'suggest'
                if suggestions:
                    text = "Here are some available slots I found:\n" + "\n".join([f"- {s['date']} {s['start_time']}" for s in suggestions])
                    text += "\nWhich of these works best for you? (reply with date and start_time e.g. 2024-01-17 15:30)"
                    return text, session
                else:
                    session['stage'] = 'no_slots'
                    return "I couldn't find available slots in the next week. Would you like to try alternative dates or be placed on a waitlist?", session
            except Exception:
                session['stage'] = 'error'
                return "Sorry — I couldn't reach the scheduling system right now. Would you like to try again later or call the clinic?", session

        if stage == 'suggest':
            parts = message.split()
            if len(parts) >= 2:
                date = parts[0]
                start_time = parts[1]
                session['collected']['date'] = date
                session['collected']['start_time'] = start_time
                session['stage'] = 'collect_contact'
                return "Great — before I book, could you share your full name, phone number, and email (one per line or comma-separated)?", session
            else:
                return "Please reply with the date and start_time from the suggestions, e.g. 2024-01-17 15:30", session

        if stage == 'collect_contact':
            parts = [p.strip() for p in message.replace('\n',',').split(',') if p.strip()]
            if len(parts) < 3:
                return "I need your name, phone, and email. Please provide them (comma-separated).", session
            name, phone, email = parts[0], parts[1], parts[2]
            session['collected']['patient'] = {"name":name, "phone": phone, "email": email}
            appointment = {
                "appointment_type": session['collected']['appointment_type'],
                "date": session['collected']['date'],
                "start_time": session['collected']['start_time'],
                "patient": session['collected']['patient'],
                "reason": session['collected'].get('reason','')
            }
            try:
                r = requests.post(f"{CAL_API}/book", json=appointment, timeout=3)
                resp = r.json()
                session['stage'] = 'done'
                # store booking id for session (mock)
                session['collected']['booking_id'] = resp.get('booking_id')
                return f"All set! Your appointment is confirmed. Confirmation code: {resp.get('confirmation_code')}\nBooking ID: {resp.get('booking_id')}", session
            except Exception:
                session['stage'] = 'error'
                return "Booking failed due to a scheduling service issue. Please try again later or call the clinic.", session

        if stage in ('done','error'):
            self.sessions.pop(session, None)
            return "If you'd like to schedule another appointment, let me know!", {}

        return "Sorry, I didn't understand. Could you rephrase?", session

    def _handle_cancel_flow(self, session, message):
        stage = session.get('stage')
        if stage == 'ask_cancel_info':
            # expect booking id or email
            token = message.strip()
            # attempt cancel via API
            try:
                payload = {}
                if '@' in token:
                    resp = requests.post(f"{CAL_API}/cancel", params={'email': token}, timeout=3)
                else:
                    resp = requests.post(f"{CAL_API}/cancel", params={'booking_id': token}, timeout=3)
                data = resp.json()
                session['stage'] = 'done'
                return f"Your appointment has been cancelled (booking_id={data.get('booking_id')}).", session
            except Exception:
                session['stage'] = 'error'
                return "Sorry, I couldn't cancel right now. Please try again later or call the clinic.", session
        return "Please provide the booking ID or the email used to book the appointment.", session

    def _handle_reschedule_flow(self, session, message):
        stage = session.get('stage')
        if stage == 'ask_booking_id':
            token = message.strip()
            session['collected']['booking_id'] = token
            session['stage'] = 'ask_new_slot_pref'
            return "Thanks — what new date/time would you like? (reply with YYYY-MM-DD HH:MM)", session
        if stage == 'ask_new_slot_pref':
            parts = message.split()
            if len(parts) >= 2:
                new_date = parts[0]
                new_start = parts[1]
                booking_id = session['collected'].get('booking_id')
                try:
                    resp = requests.post(f"{CAL_API}/reschedule", params={'booking_id': booking_id, 'new_date': new_date, 'new_start_time': new_start}, timeout=3)
                    data = resp.json()
                    session['stage'] = 'done'
                    return f"Your appointment has been rescheduled to {data.get('new_date')} at {data.get('new_start_time')}. Confirmation: {data.get('confirmation_code')}", session
                except Exception:
                    session['stage'] = 'error'
                    return "Sorry, I couldn't reschedule right now. Please try again later or call the clinic.", session
            else:
                return "Please provide the new date and start time in format YYYY-MM-DD HH:MM", session
        return "Please provide the booking ID (or email) of the appointment you'd like to reschedule.", session
