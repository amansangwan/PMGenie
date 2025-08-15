import os
import requests
from typing import Any, Dict
from dotenv import load_dotenv
load_dotenv("creds.env")

JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")

auth = (JIRA_EMAIL, JIRA_API_TOKEN)
headers = {"Accept": "application/json", "Content-Type": "application/json"}

def get_projects() -> Any:
    url = f"{JIRA_BASE_URL}/rest/api/3/project/search"
    r = requests.get(url, auth=auth, headers=headers)
    r.raise_for_status()
    data = r.json()
    # compact mapping for frontend
    return [
        {"id": p.get("id"), "key": p.get("key"), "name": p.get("name")}
        for p in data.get("values", []) or data.get("projects", []) or []
    ]

def get_project(project_id: str) -> Dict[str, Any]:
    url = f"{JIRA_BASE_URL}/rest/api/3/project/{project_id}"
    r = requests.get(url, auth=auth, headers=headers)
    r.raise_for_status()
    p = r.json()
    return {"id": p.get("id"), "key": p.get("key"), "name": p.get("name"), "projectTypeKey": p.get("projectTypeKey")}


def get_project_tickets(project_key_or_id: str) -> Any:
    # JQL to fetch issues; pagination for production (MVP: first 100)
    jql = f"project={project_key_or_id} ORDER BY updated DESC"
    url = f"{JIRA_BASE_URL}/rest/api/3/search?jql={requests.utils.quote(jql)}&maxResults=100"
    r = requests.get(url, auth=auth, headers=headers)
    r.raise_for_status()
    issues = r.json().get("issues", [])
    # minimal hierarchy projection (Epic->Story->Task/Subtask based on fields)
    def compact(issue):
        fields = issue.get("fields", {})
        return {
            "id": issue.get("id"),
            "key": issue.get("key"),
            "summary": fields.get("summary"),
            "issuetype": (fields.get("issuetype") or {}).get("name"),
            "status": (fields.get("status") or {}).get("name"),
            "parent": (fields.get("parent") or {}).get("key"),
            "epic": fields.get("epicLink") or fields.get("customfield_10014"),
        }
    return [compact(i) for i in issues]
