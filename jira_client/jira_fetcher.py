import os
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv("creds.env")

JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")

HEADERS = {
    "Authorization": f"Basic {requests.auth._basic_auth_str(JIRA_EMAIL, JIRA_API_TOKEN)}",
    "Content-Type": "application/json"
}

auth = HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)
headers = {
  "Accept": "application/json"
}


def get_projects():

    url = f"{JIRA_BASE_URL}/rest/api/3/project"
    response = requests.get(url, headers=headers, auth=auth)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return None

# def get_issues(project_key):

#     url = f"{JIRA_BASE_URL}/rest/api/3/search/jql"
#     params = {
#         "jql": f"project={project_key}",
#         "maxResults": 10,
#         'fields': '*all'
#     }

#     response = requests.get(url, headers=HEADERS,auth =auth, params=params)

#     if response.status_code == 200:
#         return response.json()["issues"]
#     else:
#         print(f"Error: {response.status_code}, {response.text}")
#         return None


def get_issues(project_key):

    url = f"{JIRA_BASE_URL}/rest/api/3/search"
    params = {
        "jql": f"project={project_key}",
        "maxResults": 100,
        "fields": "key,summary,status,priority,assignee,reporter,duedate,created,updated,issuetype,parent,labels,subtasks,issuelinks,project"
    }

    response = requests.get(url, headers=HEADERS, auth=auth, params=params)

    if response.status_code != 200:
        print(f"Error: {response.status_code}, {response.text}")
        return []

    issues = response.json().get("issues", [])
    compact_issues = []

    for issue in issues:
        fields = issue.get("fields", {})

        # Extract subtasks and blocker links (by issue key only)
        subtasks = [sub.get("key") for sub in fields.get("subtasks", [])]
        issuelinks = fields.get("issuelinks", [])
        blockers = []

        for link in issuelinks:
            if "inwardIssue" in link:
                blockers.append(link["inwardIssue"]["key"])
            elif "outwardIssue" in link:
                blockers.append(link["outwardIssue"]["key"])

        compact_issue = {
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
        }

        compact_issues.append(compact_issue)

    return compact_issues