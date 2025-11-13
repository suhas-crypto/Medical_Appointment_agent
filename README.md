# Appointment Scheduling Agent

This repository is a complete working scaffold for the Medical Appointment Scheduling Agent assessment.
It includes a FastAPI backend (with mock Calendly API endpoints), a simple RAG FAQ retriever, a stateful
scheduling conversational agent (supports scheduling, rescheduling, cancellation), and a Vite + React frontend chat UI.

## What's included
- `backend/` — FastAPI app, agent logic, RAG, tools, mock Calendly integration
- `frontend/` — Vite React chat UI (App.jsx and components)
- `data/` — `clinic_info.json`, `doctor_schedule.json`
- `architecture_diagram.png` and `architecture_diagram.pdf`
- `.env.example`, `requirements.txt`
- `tests/test_agent.py` — basic unit tests

## Quick start (development)
1. **Backend** (Windows CMD example):
```cmd
cd appointment-scheduling-agent
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```

2. **Frontend** (new terminal):
```cmd
cd appointment-scheduling-agent/frontend
npm install
npm run dev
```

Open the frontend URL printed by Vite (usually http://localhost:5173) and try messaging the agent.

## Files of interest
- `backend/agent/scheduling_agent.py` — conversation flows (schedule/reschedule/cancel + context switching)
- `backend/api/calendly_integration.py` — mock Calendly endpoints: `/api/calendly/availability`, `/book`, `/cancel`, `/reschedule`
- `backend/rag/faq_rag.py` — FAQ retriever using `data/clinic_info.json`
- `frontend/src/App.jsx` — chat UI wired to `/api/chat/message`

## System Design (summary)
- Conversation orchestrator performs intent detection, session tracking, and routes to RAG or scheduling flow.
- Tool caller abstracts availability, booking, cancel, reschedule actions to Calendly integration.
- RAG is a lightweight keyword-based retriever; swap in vector DB + embeddings for production.
- Persistence: `data/bookings.db` (SQLite) is used by mock Calendly to persist bookings.

## Notes
- This scaffold uses a mock Calendly implementation so you can run everything locally without API keys.
- To integrate a real LLM or vector DB, update the agent prompts and RAG embedding code.
- The architecture diagram is included as `architecture_diagram.png` and `architecture_diagram.pdf`.

