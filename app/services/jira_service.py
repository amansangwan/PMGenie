import os
import requests
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

# load creds.env if present (non-fatal)
load_dotenv("creds.env")

JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")

auth = (JIRA_EMAIL, JIRA_API_TOKEN)
headers = {"Accept": "application/json", "Content-Type": "application/json"}
REQUEST_TIMEOUT = 20  # seconds


def _req_get(url: str, params: Optional[Dict[str, Any]] = None) -> requests.Response:
    return requests.get(url, params=params, auth=auth, headers=headers, timeout=REQUEST_TIMEOUT)


def _req_post(url: str, payload: Dict[str, Any]) -> requests.Response:
    return requests.post(url, json=payload, auth=auth, headers=headers, timeout=REQUEST_TIMEOUT)


def get_projects() -> Any:
    """Return list of projects (compact). Uses Jira project search endpoint."""
    url = f"{JIRA_BASE_URL}/rest/api/3/project/search"
    r = _req_get(url)
    r.raise_for_status()
    data = r.json()
    return [
        {"id": p.get("id"), "key": p.get("key"), "name": p.get("name")}
        for p in data.get("values", []) or data.get("projects", []) or []
    ]


def get_project(project_id: str) -> Dict[str, Any]:
    """Return detailed project info from Jira."""
    url = f"{JIRA_BASE_URL}/rest/api/3/project/{project_id}"
    r = _req_get(url)
    r.raise_for_status()
    p = r.json()
    return {
        "id": p.get("id"),
        "key": p.get("key"),
        "name": p.get("name"),
        "description": p.get("description"),
        "projectTypeKey": p.get("projectTypeKey"),
    }


def get_project_tickets(project_key_or_id: str) -> List[Dict[str, Any]]:
    """Fetch issues for a project via JQL. Returns compact issue info."""
    jql = f"project={project_key_or_id} ORDER BY updated DESC"
    url = f"{JIRA_BASE_URL}/rest/api/3/search?jql={requests.utils.quote(jql)}&maxResults=200"
    r = _req_get(url)
    r.raise_for_status()
    issues = r.json().get("issues", [])
    def compact(issue):
        fields = issue.get("fields", {})
        epic = fields.get("epicLink") or fields.get("customfield_10014") or None
        return {
            "id": issue.get("id"),
            "key": issue.get("key"),
            "summary": fields.get("summary"),
            "issuetype": (fields.get("issuetype") or {}).get("name"),
            "status": (fields.get("status") or {}).get("name"),
            "parent": (fields.get("parent") or {}).get("key"),
            "epic": epic,
            "updated": fields.get("updated"),
        }
    return [compact(i) for i in issues]


def get_project_members(project_key_or_id: str) -> List[Dict[str, Any]]:
    """Return list of assignable users for the given project."""
    url = f"{JIRA_BASE_URL}/rest/api/3/user/assignable/search?project={requests.utils.quote(project_key_or_id)}"
    r = _req_get(url)
    r.raise_for_status()
    users = r.json()
    return [
        {"accountId": u.get("accountId"), "displayName": u.get("displayName"), "emailAddress": u.get("emailAddress")}
        for u in users
    ]


def get_create_meta(project_key: Optional[str] = None) -> Dict[str, Any]:
    """Fetch create metadata for a project (fields available for create)."""
    q = f"?projectKeys={requests.utils.quote(project_key)}&expand=projects.issuetypes.fields" if project_key else "?expand=projects.issuetypes.fields"
    url = f"{JIRA_BASE_URL}/rest/api/3/issue/createmeta{q}"
    r = _req_get(url)
    r.raise_for_status()
    return r.json()


def get_create_meta_field(project_key: str, candidate_names: List[str]) -> Optional[str]:
    """Find field key for candidate names (e.g., 'Epic Link')."""
    meta = get_create_meta(project_key)
    projects = meta.get("projects", []) or []
    for p in projects:
        for it in p.get("issuetypes", []):
            fields = it.get("fields", {})
            for fkey, fdef in fields.items():
                name = fdef.get("name", "")
                if name and any(c.lower() in name.lower() for c in candidate_names):
                    return fkey
    return None


def create_project(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Create a project in Jira. Payload should follow Jira's create project format."""
    url = f"{JIRA_BASE_URL}/rest/api/3/project"
    r = _req_post(url, payload)
    r.raise_for_status()
    return r.json()


def create_issue(
    project_key: str,
    summary: str,
    description: Optional[str],
    issuetype: str,
    parent_key: Optional[str] = None,
    epic_link: Optional[str] = None,
    extra_fields: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Generic issue creation helper. Handles epic link and parent."""
    fields: Dict[str, Any] = {
        "project": {"key": project_key},
        "summary": summary,
        "issuetype": {"name": issuetype},
    }
    if description is not None:
        fields["description"] = description
    if parent_key:
        fields["parent"] = {"key": parent_key}

    if extra_fields:
        fields.update(extra_fields)

    if epic_link:
        epic_field = get_create_meta_field(project_key, ["Epic Link", "Epic"])
        if epic_field:
            fields[epic_field] = epic_link
        else:
            fields["epicLink"] = epic_link

    payload = {"fields": fields}
    url = f"{JIRA_BASE_URL}/rest/api/3/issue"
    r = _req_post(url, payload)
    r.raise_for_status()
    return r.json()
