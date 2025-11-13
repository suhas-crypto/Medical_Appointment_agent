from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api import chat, calendly_integration

app = FastAPI(title="Appointment Scheduling Agent - Full")

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*']
)

app.include_router(calendly_integration.router, prefix='/api/calendly', tags=['calendly'])
app.include_router(chat.router, prefix='/api/chat', tags=['chat'])

@app.get('/')
def root():
    return {'message':'Appointment Scheduling Agent - Full Backend'}
