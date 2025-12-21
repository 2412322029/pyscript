from fastapi import APIRouter

from api.routes import scripts, tasks, projects

router = APIRouter()

# Include all API routes
router.include_router(scripts.router, tags=["scripts"])
router.include_router(tasks.router, tags=["tasks"])
router.include_router(projects.router, tags=["projects"])

__all__ = ["router"]
