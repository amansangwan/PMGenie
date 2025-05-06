import json
import os
import re
import time
import uuid
import openai
from dotenv import load_dotenv
from .prompts import SYSTEM_PROMPT, TOOLS
from .memory_manager import MemoryManager
# from task_manager import get_task_prioritization, get_risk_analysis
# from reports import generate_daily_standup_report

# Load API key
load_dotenv("creds.env")
openai.api_key = os.getenv("OPENAI_API_KEY")

#create client
client = openai.OpenAI()
memory = MemoryManager()
SESSION_ID = str(uuid.uuid4())
CONTEXT = {"project_name": None, "pending_query": None}

def extract_project_name(query):
    system_prompt = "You are an assistant. Extract the project name from the user input. Return only the project name. For eg. 'summarize sathi project' then return 'sathi'. If not found, return 'unknown'."
    try:

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            temperature=0
        )

        return response.choices[0].message.content.strip()
    except Exception:
        return "unknown"

def ai_reasoning_engine(user_query):
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

        # Inject past memories
        memories = memory.query_memory(
            query_text=user_query,
            top_k=3,
            project_name=project_name,
            session_id=SESSION_ID
        )
        if memories and memories[0]:
            for mem in memories[0]:
                messages.append({"role": "system", "content": f"Past Memory: {mem}"})

        # Finally the user message
        q = {'type': 'user', 'user': user_query}
        messages.append({"role": "user", "content": str(q)})

        while(True):
        # Step 3: Get AI Plan (Determine required tool(s))
            plan_response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                response_format={"type":"json_object"},
                temperature=0.2
            )
            plan_text = plan_response.choices[0].message.content
            messages.append({'role': 'assistant', 'content': plan_text})
            call = json.loads(plan_text)
            # print("---------------",call)
            if call['type'] == "output":
                memory.add_memory(
                    user_input=user_query,
                    ai_response=call['output'],
                    project_name=project_name,
                    session_id=SESSION_ID,
                    tags="jira_summary"
                )

                return call['output']
                # print('🤖', call['output'])
                # break
            elif call['type'] == "action":
                # print(call)
                fn = TOOLS[call['function']]['func']
                # if 'input' in call and call['input'] != '':  # Only pass input if it's non-empty
                #     observation = fn(call['input'])
                # else:
                #     # If no input is needed (like getProjects or getCurrentDate), just call the function
                #     observation = fn()
                if(TOOLS[call['function']]['needs_input']):

                    observation = fn(call['input'])

                else:
                    observation = fn()
                obs = {'type':'observation', "observation":observation}
                messages.append({'role': 'developer', 'content': str(obs)})



    except Exception as e:
        return f"Error: {str(e)}"