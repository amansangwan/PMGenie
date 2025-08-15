import os
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv("creds.env")

JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")

if not all([JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN]):
    raise ValueError("Missing one or more Jira credentials in creds.env")

auth = HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)
HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": f"Basic {requests.auth._basic_auth_str(JIRA_EMAIL, JIRA_API_TOKEN)}"
}


def get_projects():
    """Fetch all Jira projects visible to the user."""
    url = f"{JIRA_BASE_URL}/rest/api/3/project"
    try:
        response = requests.get(url, headers=HEADERS, auth=auth, timeout=10)
        if response.status_code == 200:
            return response.json()
        print(f"[JIRA] Failed to fetch projects: {response.status_code} - {response.text}")
        return []
    except requests.RequestException as e:
        print(f"[JIRA] Exception while fetching projects: {e}")
        return []


def get_issues(project_key, max_results_per_page=100):
    """
    Fetch all issues for a project with pagination support.
    Jira limits results to 100 per request.
    """
    url = f"{JIRA_BASE_URL}/rest/api/3/search"
    start_at = 0
    all_issues = []

    while True:
        params = {
            "jql": f"project={project_key}",
            "maxResults": max_results_per_page,
            "startAt": start_at,
            "fields": "key,summary,status,priority,assignee,reporter,duedate,created,updated,issuetype,parent,labels,subtasks,issuelinks,project"
        }

        try:
            response = requests.get(url, headers=HEADERS, auth=auth, params=params, timeout=15)
            if response.status_code != 200:
                print(f"[JIRA] Failed to fetch issues: {response.status_code} - {response.text}")
                break

            data = response.json()
            issues = data.get("issues", [])

            if not issues:
                break  # No more issues

            for issue in issues:
                fields = issue.get("fields", {})

                subtasks = [sub.get("key") for sub in fields.get("subtasks", [])]
                blockers = []
                for link in fields.get("issuelinks", []):
                    if "inwardIssue" in link:
                        blockers.append(link["inwardIssue"]["key"])
                    elif "outwardIssue" in link:
                        blockers.append(link["outwardIssue"]["key"])

                all_issues.append({
                    "key": issue.get("key"),
                    "summary": fields.get("summary"),
                    "status": fields.get("status", {}).get("name"),
                    "priority": fields.get("priority", {}).get("name"),
                    "assignee": fields.get("assignee", {}).get("displayName") if fields.get("assignee") else "Unassigned",
                    "reporter": fields.get("reporter", {}).get("displayName") if fields.get("reporter") else None,
                    "duedate": fields.get("duedate"),
                    "created": fields.get("created"),
                    "updated": fields.get("updated"),
                    "subtasks": subtasks,
                    "parent": fields.get("parent", {}).get("key") if fields.get("parent") else None,
                    "blockers": blockers,
                    "labels": fields.get("labels", []),
                    "issue_type": fields.get("issuetype", {}).get("name"),
                    "project": fields.get("project", {}).get("name")
                })

            # Move to next page
            start_at += max_results_per_page

            # Stop if we fetched all
            if start_at >= data.get("total", 0):
                break

        except requests.RequestException as e:
            print(f"[JIRA] Exception while fetching issues: {e}")
            break

    return all_issues
