"""
任务管理模块 - 使用huey进行异步任务处理
"""

import os
import sys
from datetime import timedelta
from typing import Optional

from huey import RedisHuey
from huey import crontab
from huey.api import Task
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置Redis连接
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/1")

# 创建Huey实例
huey_app = RedisHuey(
    "python-script-runner",
    url=redis_url,
    results=True,
    store_none=True,
    utc=True,
)


@huey_app.task()
def run_python_script(script_content: str, script_id: str = None) -> dict:
    """
    执行Python脚本的异步任务

    Args:
        script_content: Python脚本内容
        script_id: 脚本ID（可选）

    Returns:
        dict: 包含执行结果、输出和错误信息的字典
    """
    import io
    import traceback

    result = {
        "script_id": script_id,
        "success": True,
        "output": "",
        "error": None,
        "result": None,
    }

    # 重定向标准输出
    stdout_backup = sys.stdout
    stderr_backup = sys.stderr

    captured_output = io.StringIO()
    sys.stdout = captured_output
    sys.stderr = captured_output

    try:
        # 执行脚本
        exec_globals = {}
        exec(script_content, exec_globals)

        # 如果有__result__变量，使用它作为结果
        result["result"] = exec_globals.get("__result__", None)

    except Exception as e:
        result["success"] = False
        result["error"] = str(e)
        result["traceback"] = traceback.format_exc()
    finally:
        # 恢复标准输出
        sys.stdout = stdout_backup
        sys.stderr = stderr_backup

        # 获取捕获的输出
        result["output"] = captured_output.getvalue()
        captured_output.close()

    return result


@huey_app.task(retries=3, retry_delay=60)  # 最多重试3次，每次间隔60秒
def process_script_result(task_id: str, script_id: str) -> Optional[bool]:
    """
    处理脚本执行结果的任务

    Args:
        task_id: huey任务ID
        script_id: 脚本ID

    Returns:
        bool: 处理是否成功
    """
    try:
        # 获取任务结果
        task: Task = huey_app.storage.get_task(task_id)
        if not task:
            return False

        # 这里可以添加结果处理逻辑，例如保存到数据库、发送通知等
        print(f"Processing result for script {script_id} with task {task_id}")

        return True
    except Exception as e:
        print(f"Error processing script result: {e}")
        # 会根据上面的装饰器配置自动重试
        raise


@huey_app.periodic_task(crontab(minute=0))  # 每小时执行一次
def cleanup_old_tasks():
    """
    清理旧任务的定时任务
    """
    # 这里可以添加清理旧任务的逻辑
    print("Running cleanup task")


# 如果作为主模块运行，启动消费者
if __name__ == "__main__":
    import sys
    from huey.consumer import Consumer

    consumer = Consumer(huey_app)
    consumer.run()
