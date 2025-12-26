import asyncio
import logging
import os
from contextlib import asynccontextmanager

from api.routes import api_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from middleware.exception_handlers import register_exception_handlers
from middleware.logging_config import configure_logging

# Local imports
from models.database import init_db

# Database imports
# Task queue imports
from tasks import cleanup_old_tasks

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Configure logging
logging_config = configure_logging()


# Lifespan event handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logging.info("Starting up Python Script Execution Service")
    asyncio.create_task(periodic_cleanup())
    yield
    # Shutdown logic
    logging.info("Shutting down Python Script Execution Service")


# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Python Script Execution Service",
    description="A service to execute Python scripts asynchronously",
    version="1.0.0",
    logging_config=logging_config,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # 更新为Vue前端端口
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register exception handlers
register_exception_handlers(app)

# Include API routes
app.include_router(api_router, prefix="/api")
init_db()


async def periodic_cleanup():
    """Periodically cleanup old tasks"""
    while True:
        try:
            # Queue the cleanup task
            cleanup_old_tasks()
            logger.info("Queued task cleanup")
        except Exception as e:
            logger.error(f"Error during task cleanup: {e}")
        # Wait for 1 hour before next cleanup
        await asyncio.sleep(3600)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
