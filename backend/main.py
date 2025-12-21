from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os
from typing import Dict, Any, List

# 导入huey任务
from tasks import huey_app, run_python_script, process_script_result

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

# 配置数据库连接
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./scripts.db")
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 创建FastAPI应用
app = FastAPI(
    title="Python Script Runner API",
    description="一个支持Python脚本异步执行的后端服务",
    version="0.1.0"
)

# 配置CORS
# 允许所有来源访问API，在生产环境中应该限制为特定的域名
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中替换为前端应用的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据库依赖项
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def read_root():
    return {"message": "Welcome to Python Script Runner API"}


@app.post("/scripts/run", response_model=Dict[str, Any])
def run_script(script_data: Dict[str, str], background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    异步执行Python脚本
    
    Args:
        script_data: 包含脚本内容和可选脚本ID的字典
        background_tasks: FastAPI后台任务
        db: 数据库会话
    
    Returns:
        包含任务ID的响应
    """
    script_content = script_data.get("content", "")
    script_id = script_data.get("id")
    
    if not script_content:
        raise HTTPException(status_code=400, detail="Script content is required")
    
    # 异步执行脚本
    task = run_python_script.schedule(args=(script_content, script_id))
    
    # 添加任务处理结果的后台任务
    background_tasks.add_task(
        process_script_result,
        task.task_id,
        script_id or task.task_id
    )
    
    return {
        "task_id": task.task_id,
        "script_id": script_id,
        "status": "scheduled",
        "message": "Script execution has been scheduled"
    }


@app.get("/tasks/{task_id}", response_model=Dict[str, Any])
def get_task_status(task_id: str):
    """
    获取任务执行状态
    
    Args:
        task_id: 任务ID
    
    Returns:
        任务状态信息
    """
    # 获取任务
    task = huey_app.storage.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # 构建响应
    response = {
        "task_id": task_id,
        "status": task.status,
        "created_at": task.enqueued_at.isoformat() if task.enqueued_at else None,
        "started_at": task.started_at.isoformat() if task.started_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
    }
    
    # 如果任务完成，获取结果
    if task.is_completed:
        try:
            result = huey_app.result(task_id)
            response["result"] = result
        except Exception as e:
            response["error"] = str(e)
    
    return response


@app.post("/scripts/batch", response_model=Dict[str, Any])
def batch_run_scripts(scripts: List[Dict[str, str]], background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    批量执行Python脚本
    
    Args:
        scripts: 脚本列表
        background_tasks: FastAPI后台任务
        db: 数据库会话
    
    Returns:
        任务ID列表
    """
    task_ids = []
    
    for script_data in scripts:
        script_content = script_data.get("content", "")
        script_id = script_data.get("id")
        
        if script_content:
            task = run_python_script.schedule(args=(script_content, script_id))
            task_ids.append(task.task_id)
            
            # 添加结果处理任务
            background_tasks.add_task(
                process_script_result,
                task.task_id,
                script_id or task.task_id
            )
    
    return {
        "task_ids": task_ids,
        "count": len(task_ids),
        "status": "scheduled",
        "message": f"{len(task_ids)} scripts have been scheduled for execution"
    }


# 健康检查端点
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Python Script Runner API",
        "version": "0.1.0"
    }


# 如果作为主模块运行
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)