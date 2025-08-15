from typing import List, Dict, Any
from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv("creds.env")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# IMPORTANT: Wire this to your existing agent logic.
# If your function path differs, adjust the import below.
try:
    from ai_reasoning_engine.ai_engine import ai_reasoning_engine  # expected function
except Exception:
    ai_reasoning_engine = None

async def run_ai_message(query: str, context_docs: List[str] | None = None) -> str:
    print("inside run_ai_message")
    # If your custom agent exists, call it; else fallback to a simple LLM completion.
    if ai_reasoning_engine:
        response = ai_reasoning_engine(user_query=query)
        return response

    # Fallback minimal answer

    system = "You are a helpful assistant."
    msgs = [{"role": "system", "content": system}, {"role": "user", "content": query}]
    resp = client.chat.completions.create(model="gpt-4o-mini", messages=msgs)
    return resp.choices[0].message.content