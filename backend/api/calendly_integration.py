from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from datetime import datetime, timedelta
import json, os

router = APIRouter()

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
SCHEDULE_FILE = os.path.join(DATA_DIR, "doctor_schedule.json")

def load_schedule():
    try:
        with open(SCHEDULE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"default":[]}

@router.get("/availability")
def availability(date: Optional[str] = Query(None), appointment_type: Optional[str] = Query("consultation")):
    """Return available slots for a date (mock). If date omitted, returns next 7 days."""
    schedule = load_schedule()
    if date:
        try:
            d = datetime.fromisoformat(date).date()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        days = [d]
    else:
        today = datetime.now().date()
        days = [today + timedelta(days=i) for i in range(0, 7)]

    results = []
    for day in days:
        day_str = day.isoformat()
        day_slots = schedule.get(day_str, schedule.get("default", []))
        available = []
        for s in day_slots:
            if s.get("available", True):
                available.append({"start_time": s["start_time"], "end_time": s["end_time"], "available": True})
        results.append({"date": day_str, "available_slots": available})
    return {"dates": results}

@router.post("/book")
def book(appointment: dict):
    """Mock booking: returns confirmation and writes to schedule as booked (non-persistent)."""
    date = appointment.get("date")
    start_time = appointment.get("start_time")
    if not date or not start_time:
        raise HTTPException(status_code=400, detail="date and start_time required")
    confirmation = {
        "booking_id": f"APPT-{int(datetime.now().timestamp())}",
        "status": "confirmed",
        "confirmation_code": "MOCK123",
        "details": appointment
    }
    return confirmation

@router.post("/cancel")
def cancel(booking_id: str = None, email: Optional[str] = None):
    """Mock cancellation. Require booking_id or email + date to cancel."""
    if not booking_id and not email:
        raise HTTPException(status_code=400, detail="booking_id or email required to cancel")
    # In a real system, you'd look up booking and mark cancelled. Here return success.
    return {"status":"cancelled","booking_id": booking_id, "by": email}

@router.post("/reschedule")
def reschedule(booking_id: str = None, new_date: Optional[str] = None, new_start_time: Optional[str] = None):
    """Mock rescheduling. Require booking_id and new slot info."""
    if not booking_id or not new_date or not new_start_time:
        raise HTTPException(status_code=400, detail="booking_id, new_date and new_start_time required")
    confirmation = {
        "booking_id": booking_id,
        "status": "rescheduled",
        "new_date": new_date,
        "new_start_time": new_start_time,
        "confirmation_code": "MOCK-RESCH-123"
    }
    return confirmation
