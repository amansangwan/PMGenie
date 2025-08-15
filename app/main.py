from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.auth import router as auth_router
from app.routes.ai import router as ai_router
from app.routes.knowledge_base import router as kb_router
from app.routes.projects import router as projects_router
from app.db.session import init_db

app = FastAPI(title="PMGenie API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    init_db()

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(ai_router, prefix="/ai", tags=["ai"])
app.include_router(kb_router, prefix="/knowledge-base", tags=["knowledge-base"])
app.include_router(projects_router, prefix="/projects", tags=["projects"])
