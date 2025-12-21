from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import asyncio
import os
import logging
import json
import traceback
from typing import Dict, Any, Optional, List

# Database imports
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

# Task queue imports
from huey import RedisHuey
from tasks import run_python_script, process_script_result, cleanup_old_tasks

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./pyscript.db")
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Huey configuration
from tasks import huey_app as huey

# Local imports
from models.database import get_db, engine
from models.models import Base
from services.script_execution_service import ScriptExecutionService
from tasks import cleanup_old_tasks
from middleware.exception_handlers import register_exception_handlers
from api.api import router as api_router
from middleware.logging_config import configure_logging

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

# Create database tables
Base.metadata.create_all(bind=engine)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register exception handlers
register_exception_handlers(app)

# Include API routes
app.include_router(api_router, prefix="/api")

# Initialize services
script_service = ScriptExecutionService()


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

    uvicorn.run(app, host="0.0.0.0", port=8000)
