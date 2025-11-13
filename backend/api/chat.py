from fastapi import APIRouter
from pydantic import BaseModel
from ..agent.scheduling_agent import SchedulingAgent

router = APIRouter()
agent = SchedulingAgent()

class ChatRequest(BaseModel):
    user_id: str
    message: str
    context: dict = {}

@router.post("/message")
def message(req: ChatRequest):
    response, context = agent.handle_message(req.user_id, req.message, req.context)
    return {"response": response, "context": context}
