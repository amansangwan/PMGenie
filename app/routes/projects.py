from fastapi import APIRouter, Depends
from app.routes.deps import get_current_user_id
from app.services.jira_service import get_projects, get_project, get_project_tickets

router = APIRouter()

@router.get("")
def list_projects(user_id: int = Depends(get_current_user_id)):
    return get_projects()

@router.get("/{projectId}")
def project_detail(projectId: str, user_id: int = Depends(get_current_user_id)):
    return get_project(projectId)

@router.get("/{projectId}/tickets")
def project_tickets(projectId: str, user_id: int = Depends(get_current_user_id)):
    return get_project_tickets(projectId)
