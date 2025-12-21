from fastapi import APIRouter

from api.routes import scripts, tasks, projects, flow

api_router = APIRouter()

api_router.include_router(scripts.router, tags=["scripts"])
api_router.include_router(tasks.router, tags=["tasks"])
api_router.include_router(projects.router, tags=["projects"])
api_router.include_router(flow.router, tags=["flows"])

__all__ = ["api_router"]


