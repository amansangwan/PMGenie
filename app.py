# app.py

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from ai_reasoning_engine.ai_engine import ai_reasoning_engine

app = FastAPI()

# Allow frontend (e.g., from Vercel)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with Vercel domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryInput(BaseModel):
    query: str

@app.post("/chat")
async def chat_endpoint(input: QueryInput):
    response = ai_reasoning_engine(input.query)
    return {"response": response}
