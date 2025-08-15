# ai_reasoning_engine/ai_engine.py
import json
import os
import uuid
from dotenv import load_dotenv
from openai import OpenAI
from ai_reasoning_engine.prompts import SYSTEM_PROMPT, TOOLS
from ai_reasoning_engine.memory_manager import MemoryManager
# Load env once
load_dotenv("creds.env")

# Create client explicitly; do NOT rely on global openai.api_key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

memory = MemoryManager()  # uses its own client internally (we’ll fix below)
SESSION_ID = str(uuid.uuid4())
CONTEXT = {"project_name": None, "pending_query": None}

def extract_project_name(query: str) -> str:
    system_prompt = (
        "You are an assistant. Extract the project name from the user input. "
        "Return only the project name. If not found, return 'unknown'."
    )
    try:
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query},
            ],
            temperature=0,
        )
        return (resp.choices[0].message.content or "unknown").strip()
    except Exception:
        return "unknown"

def ai_reasoning_engine(user_query: str) -> str:
    """
    AI reasoning engine that follows START, PLAN, ACTION, OBSERVATION, and OUTPUT states dynamically.
    :param user_query: User's request (e.g., "Summarize Jira updates for Sarthi project")
    :return: Structured AI response
    """
    try:
        detected_project = extract_project_name(user_query)
        if detected_project.lower() != "unknown":
            CONTEXT["project_name"] = detected_project

        project_name = CONTEXT["project_name"]
        if project_name is None:
            CONTEXT["pending_query"] = user_query

        # If the user just provided a project name *and* we have a pending query,
        # swap user_query with that pending intent and clear pending.
        if project_name and CONTEXT["pending_query"]:
            user_query = CONTEXT["pending_query"]
            CONTEXT["pending_query"] = None

        # Build messages with explicit project context
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if project_name:
            messages.append({
                "role": "system",
                "content": f"Current project context: {project_name}"
            })

        # Context from memory
        memories = memory.query_memory(
            query_text=user_query, top_k=3,
            project_name=project_name, session_id=SESSION_ID
        )
        if memories and memories[0]:
            for mem in memories[0]:
                messages.append({"role": "system", "content": f"Past Memory: {mem}"})

        # User input
        messages.append({"role": "user", "content": json.dumps({"type": "user", "user": user_query})})

        # Safety valve to avoid infinite loops
        MAX_ITERS = 100

        for _ in range(MAX_ITERS):
            plan_response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            plan_text = plan_response.choices[0].message.content
            messages.append({'role': 'assistant', 'content': plan_text})
            call = json.loads(plan_text or "{}")

            if call.get('type') == "output":
                memory.add_memory(
                    user_input=user_query,
                    ai_response=call.get('output', ''),
                    project_name=project_name,
                    session_id=SESSION_ID,
                    tags="jira_summary",
                )
                return call.get('output', '')

            if call.get('type') == "action":
                fn_name = call.get('function')
                fn = TOOLS[fn_name]['func']
                if TOOLS[fn_name]['needs_input']:
                    observation = fn(call.get('input'))
                else:
                    observation = fn()
                obs = {'type': 'observation', 'observation': observation}
                messages.append({'role': 'developer', 'content': json.dumps(obs)})
                continue

        return "I reached the maximum reasoning steps without a final output. Try refining the query."

    except Exception as e:
        return f"Error: {str(e)}"
