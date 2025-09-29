from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any, Dict, List
from datetime import datetime

from app.routes.deps import get_current_user_id
from app.db.session import get_db
from app.services import jira_service
from app.models.chat import ChatMessage
from app.schemas.project import (
    ProjectCreateRequest,
    EpicCreateRequest,
    StoryCreateRequest,
    TaskCreateRequest,
    SubtaskCreateRequest,
    ProjectSummaryResponse,
    ProjectDetailResponse,
)

router = APIRouter(tags=["projects"])


# --------------------------
# Helper to compute counts
# --------------------------
def compute_counts_and_progress(issues: List[Dict[str, Any]]) -> Dict[str, Any]:
    counts = {"Epic": 0, "Story": 0, "Task": 0, "Sub-task": 0, "Other": 0}
    status_counts: Dict[str, int] = {}
    total = 0
    done = 0
    for i in issues:
        itype = (i.get("issuetype") or "Other")
        counts[itype] = counts.get(itype, 0) + 1
        total += 1
        status = i.get("status") or "Unknown"
        status_counts[status] = status_counts.get(status, 0) + 1
        if "done" in status.lower():
            done += 1
    progress = (done / total * 100.0) if total > 0 else 0.0
    return {"counts": counts, "status_counts": status_counts, "progress": progress}


# --------------------------
# GET: list projects (proxy to Jira)
# --------------------------
@router.get("", response_model=List[ProjectSummaryResponse])
def list_projects(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    try:
        return jira_service.get_projects()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))


# --------------------------
# GET: project detail (proxy + local aggregates)
# --------------------------
@router.get("/{project_key}", response_model=ProjectDetailResponse)
def get_project_detail(project_key: str, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    try:
        jira_proj = jira_service.get_project(project_key)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Error fetching project from Jira: {str(e)}")

    try:
        issues = jira_service.get_project_tickets(project_key)
    except Exception:
        issues = []

    agg = compute_counts_and_progress(issues)

    # local message stats
    try:
        messages_count = db.query(ChatMessage).filter(ChatMessage.project_id == project_key).count()
        last_message = (
            db.query(ChatMessage)
            .filter(ChatMessage.project_id == project_key)
            .order_by(ChatMessage.created_at.desc())
            .first()
        )
        last_chat_ts = last_message.created_at if last_message else None
    except Exception:
        messages_count = 0
        last_chat_ts = None

    # issue last updated
    issue_last_updated = None
    for i in issues:
        if i.get("updated"):
            try:
                t = datetime.fromisoformat(i["updated"].replace("Z", "+00:00"))
                if issue_last_updated is None or t > issue_last_updated:
                    issue_last_updated = t
            except Exception:
                pass

    last_activity = None
    if issue_last_updated and last_chat_ts:
        last_activity = max(issue_last_updated, last_chat_ts)
    else:
        last_activity = issue_last_updated or last_chat_ts

    # members
    try:
        members = jira_service.get_project_members(project_key)
    except Exception:
        members = []

    return {
        "id": jira_proj.get("id"),
        "key": jira_proj.get("key"),
        "name": jira_proj.get("name"),
        "description": jira_proj.get("description"),
        "projectTypeKey": jira_proj.get("projectTypeKey"),
        "counts": agg["counts"],
        "status_counts": agg["status_counts"],
        "progress": agg["progress"],
        "members": members,
        "messages_count": messages_count,
        "last_activity": last_activity,
        "due_date": None,
    }


# --------------------------
# POST: create a Jira project (proxy)
# --------------------------
@router.post("", status_code=status.HTTP_201_CREATED)
def post_create_project(req: ProjectCreateRequest, user_id: int = Depends(get_current_user_id)):
    payload = {
        "name": req.name,
        "description": req.description or "",
    }
    try:
        created = jira_service.create_project(payload)
        return created
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Error creating project in Jira: {str(e)}")


# --------------------------
# POST: create Epic in Jira
# --------------------------
@router.post("/{project_key}/epics", status_code=status.HTTP_201_CREATED)
def post_create_epic(project_key: str, req: EpicCreateRequest, user_id: int = Depends(get_current_user_id)):
    try:
        created = jira_service.create_issue(
            project_key=project_key,
            summary=req.title,
            description=req.description,
            issuetype="Epic",
        )
        return created
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Error creating epic in Jira: {str(e)}")


# --------------------------
# POST: create Story in Jira and attempt to link to Epic
# --------------------------
@router.post("/{project_key}/epics/{epic_key}/stories", status_code=status.HTTP_201_CREATED)
def post_create_story_under_epic(project_key: str, epic_key: str, req: StoryCreateRequest, user_id: int = Depends(get_current_user_id)):
    try:
        created = jira_service.create_issue(
            project_key=project_key,
            summary=req.title,
            description=req.description,
            issuetype="Story",
            epic_link=epic_key,
        )
        return created
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Error creating story in Jira: {str(e)}")


# --------------------------
# POST: create Task
# --------------------------
@router.post("/{project_key}/stories/{story_key}/tasks", status_code=status.HTTP_201_CREATED)
def post_create_task_under_story(project_key: str, story_key: str, req: TaskCreateRequest, user_id: int = Depends(get_current_user_id)):
    try:
        created = jira_service.create_issue(
            project_key=project_key,
            summary=req.title,
            description=req.description,
            issuetype="Task",
        )
        return created
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Error creating task in Jira: {str(e)}")


# --------------------------
# POST: create Subtask
# --------------------------
@router.post("/{project_key}/tasks/{task_key}/subtasks", status_code=status.HTTP_201_CREATED)
def post_create_subtask_under_task(project_key: str, task_key: str, req: SubtaskCreateRequest, user_id: int = Depends(get_current_user_id)):
    try:
        created = jira_service.create_issue(
            project_key=project_key,
            summary=req.title,
            description=req.description,
            issuetype="Sub-task",
            parent_key=task_key,
        )
        return created
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Error creating subtask in Jira: {str(e)}")
