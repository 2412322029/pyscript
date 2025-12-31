from api.routes import flow, projects, scripts, tasks
from fastapi import APIRouter

api_router = APIRouter()

# 注册各模块路由
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(scripts.router, prefix="/scripts", tags=["scripts"])
# api_router.include_router(displays.router, prefix="/displays", tags=["displays"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(flow.router, prefix="/flows", tags=["flows"])

__all__ = ["api_router"]