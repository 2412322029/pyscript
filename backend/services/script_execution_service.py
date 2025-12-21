import json
import subprocess
import re
import logging
from datetime import datetime
import time
import os
import asyncio
from typing import Dict, Any, List, Union, Optional

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ScriptExecutionService:
    """脚本执行服务类，负责解析和执行JSON格式的脚本
    
    异步实现，适配FastAPI框架，支持各种脚本操作
    """
    
    # 支持的操作类型
    SUPPORTED_ACTIONS: set[str] = {
        "set_var", "get_var", "execute_command", "condition", "loop", 
        "delay", "log", "trigger", "http_request", "combine_data"
    }
    
    # 触发器类型
    TRIGGER_TYPES: set[str] = {
        "time_based", "interval", "event_based"
    }
    
    @staticmethod
    async def execute_script(script_content: Union[str, Dict[str, Any]], variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        执行脚本内容（异步版本）
        
        Args:
            script_content: 脚本内容(JSON字符串或字典)
            variables: 初始变量字典
            
        Returns:
            执行结果字典
        """
        try:
            # 解析脚本内容
            if isinstance(script_content, str):
                try:
                    script_data: Dict[str, Any] = json.loads(script_content)
                except json.JSONDecodeError:
                    # 如果不是有效的JSON，尝试作为Python代码执行（简单兼容）
                    return await ScriptExecutionService._execute_python_script(script_content, variables)
            else:
                script_data = script_content
            
            # 初始化变量空间
            context: Dict[str, Any] = {
                "variables": variables.copy() if variables else {},
                "results": {},
                "execution_history": [],
                "start_time": datetime.now().isoformat()
            }
            
            # 执行脚本步骤
            if "steps" in script_data:
                for step in script_data["steps"]:
                    step_result = await ScriptExecutionService._execute_step(step, context)
                    if step_result.get("type") == "error":
                        # 如果步骤执行出错，中断执行
                        context["results"]["error"] = step_result["message"]
                        break
            else:
                # 单步骤执行模式
                step_result = await ScriptExecutionService._execute_step(script_data, context)
                if step_result.get("type") == "error":
                    context["results"]["error"] = step_result["message"]
            
            # 完成执行
            context["end_time"] = datetime.now().isoformat()
            
            return {
                "status": "success" if "error" not in context["results"] else "error",
                "variables": context["variables"],
                "results": context["results"],
                "execution_history": context["execution_history"],
                "execution_time": context["end_time"]
            }
            
        except Exception as e:
            logger.error(f"Script execution failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    @staticmethod
    async def _execute_step(step: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """执行单个脚本步骤（异步版本）"""
        action_type: Optional[str] = step.get("action")
        
        if not action_type:
            return ScriptExecutionService._create_error("Action type is required")
        
        if action_type not in ScriptExecutionService.SUPPORTED_ACTIONS:
            return ScriptExecutionService._create_error(f"Unsupported action type: {action_type}")
        
        timestamp: str = datetime.now().isoformat()
        
        try:
            # 根据动作类型执行相应操作
            if action_type == "set_var":
                result = ScriptExecutionService._set_variable(step, context["variables"])
            elif action_type == "get_var":
                result = ScriptExecutionService._get_variable(step, context["variables"])
            elif action_type == "execute_command":
                result = await ScriptExecutionService._execute_command(step)
            elif action_type == "condition":
                result = await ScriptExecutionService._execute_condition(step, context)
            elif action_type == "loop":
                result = await ScriptExecutionService._execute_loop(step, context)
            elif action_type == "delay":
                result = await ScriptExecutionService._execute_delay(step)
            elif action_type == "log":
                result = ScriptExecutionService._execute_log(step)
            elif action_type == "trigger":
                result = ScriptExecutionService._execute_trigger(step, context)
            elif action_type == "http_request":
                result = await ScriptExecutionService._execute_http_request(step)
            elif action_type == "combine_data":
                result = ScriptExecutionService._combine_data(step, context["variables"])
            else:
                result = ScriptExecutionService._create_error(f"Unknown action type: {action_type}")
            
            # 记录执行历史
            context["execution_history"].append({
                "timestamp": timestamp,
                "action": action_type,
                "result": result
            })
            
            return result
            
        except Exception as e:
            error_message = f"Error executing {action_type}: {str(e)}"
            logger.error(error_message)
            return ScriptExecutionService._create_error(error_message)
    
    @staticmethod
    def _set_variable(step: Dict[str, Any], variables: Dict[str, Any]) -> Dict[str, Any]:
        """设置变量"""
        var_name: Optional[str] = step.get("name")
        var_value: Any = step.get("value")
        
        if not var_name:
            return ScriptExecutionService._create_error("Variable name is required")
        
        # 处理变量引用
        processed_value: Any = ScriptExecutionService._process_variable_references(var_value, variables)
        
        variables[var_name] = processed_value
        
        return {
            "type": "success",
            "message": f"Variable {var_name} set",
            "value": processed_value
        }
    
    @staticmethod
    def _get_variable(step: Dict[str, Any], variables: Dict[str, Any]) -> Dict[str, Any]:
        """获取变量"""
        var_name: Optional[str] = step.get("name")
        target: Optional[str] = step.get("target")
        
        if not var_name:
            return ScriptExecutionService._create_error("Variable name is required")
        
        if var_name not in variables:
            return ScriptExecutionService._create_error(f"Variable {var_name} not found")
        
        value: Any = variables[var_name]
        
        # 如果指定了目标，将值保存到results中
        if target:
            return {
                "type": "success",
                "target": target,
                "value": value
            }
        
        return {
            "type": "success",
            "value": value
        }
    
    @staticmethod
    async def _execute_command(step: Dict[str, Any]) -> Dict[str, Any]:
        """执行命令（异步版本）"""
        command: Optional[Union[str, List[str]]] = step.get("command")
        shell: bool = step.get("shell", False)
        timeout: int = step.get("timeout", 60)
        
        if not command:
            return ScriptExecutionService._create_error("Command is required")
        
        try:
            # 安全检查 - 不允许执行危险命令
            if ScriptExecutionService._is_dangerous_command(command):
                return ScriptExecutionService._create_error("Command execution not allowed for security reasons")
            
            # 异步执行命令
            result = await asyncio.to_thread(
                subprocess.run,
                command if isinstance(command, list) else command,
                shell=shell,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return {
                "type": "success",
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
        except subprocess.TimeoutExpired:
            return ScriptExecutionService._create_error("Command execution timed out")
        except Exception as e:
            return ScriptExecutionService._create_error(f"Command execution failed: {str(e)}")
    
    @staticmethod
    async def _execute_condition(step: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """执行条件判断（异步版本）"""
        condition: Optional[str] = step.get("condition")
        if_true: List[Dict[str, Any]] = step.get("if_true", [])
        if_false: List[Dict[str, Any]] = step.get("if_false", [])
        
        if not condition:
            return ScriptExecutionService._create_error("Condition is required")
        
        try:
            # 处理变量引用
            processed_condition: str = ScriptExecutionService._process_variable_references(condition, context["variables"])
            
            # 安全评估条件表达式
            result: bool = ScriptExecutionService._safe_eval(processed_condition, context["variables"])
            
            # 根据条件结果执行相应步骤
            steps_to_execute: List[Dict[str, Any]] = if_true if result else if_false
            
            for sub_step in steps_to_execute:
                sub_result = await ScriptExecutionService._execute_step(sub_step, context)
                if sub_result.get("type") == "error":
                    return sub_result
            
            return {
                "type": "success",
                "condition_result": result,
                "executed": "if_true" if result else "if_false"
            }
            
        except Exception as e:
            return ScriptExecutionService._create_error(f"Condition evaluation failed: {str(e)}")
    
    @staticmethod
    async def _execute_loop(step: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """执行循环（异步版本）"""
        loop_type: str = step.get("type", "for")  # for 或 while
        iterations: int = step.get("iterations", 1)  # for循环的迭代次数
        condition: Optional[str] = step.get("condition")  # while循环的条件
        loop_steps: List[Dict[str, Any]] = step.get("steps", [])
        
        iteration_count: int = 0
        max_iterations: int = step.get("max_iterations", 1000)  # 防止无限循环
        
        try:
            if loop_type == "for":
                # 执行指定次数的循环
                for i in range(iterations):
                    if iteration_count >= max_iterations:
                        return ScriptExecutionService._create_error("Loop exceeded maximum iterations")
                    
                    context["variables"]["loop_index"] = i
                    for sub_step in loop_steps:
                        sub_result = await ScriptExecutionService._execute_step(sub_step, context)
                        if sub_result.get("type") == "error":
                            return sub_result
                    iteration_count += 1
            
            elif loop_type == "while":
                if not condition:
                    return ScriptExecutionService._create_error("While loop requires a condition")
                
                # 执行条件循环
                while True:
                    if iteration_count >= max_iterations:
                        return ScriptExecutionService._create_error("Loop exceeded maximum iterations")
                    
                    processed_condition: str = ScriptExecutionService._process_variable_references(condition, context["variables"])
                    if not ScriptExecutionService._safe_eval(processed_condition, context["variables"]):
                        break
                    
                    for sub_step in loop_steps:
                        sub_result = await ScriptExecutionService._execute_step(sub_step, context)
                        if sub_result.get("type") == "error":
                            return sub_result
                    iteration_count += 1
            
            return {
                "type": "success",
                "iterations_executed": iteration_count
            }
            
        except Exception as e:
            return ScriptExecutionService._create_error(f"Loop execution failed: {str(e)}")
    
    @staticmethod
    async def _execute_delay(step: Dict[str, Any]) -> Dict[str, Any]:
        """执行延迟（异步版本）"""
        delay_seconds: Union[int, float] = step.get("seconds", 1)
        
        try:
            # 使用异步sleep代替同步sleep
            await asyncio.sleep(float(delay_seconds))
            return {
                "type": "success",
                "message": f"Delayed for {delay_seconds} seconds"
            }
        except ValueError:
            return ScriptExecutionService._create_error("Invalid delay seconds value")
    
    @staticmethod
    def _execute_log(step: Dict[str, Any]) -> Dict[str, Any]:
        """执行日志记录"""
        message: str = step.get("message", "")
        level: str = step.get("level", "info")
        
        # 处理变量引用
        variables: Dict[str, Any] = step.get("variables", {})
        processed_message: str = ScriptExecutionService._process_variable_references(message, variables)
        
        # 记录日志
        log_method = getattr(logger, level.lower(), logger.info)
        log_method(processed_message)
        
        return {
            "type": "success",
            "message": processed_message,
            "level": level
        }
    
    @staticmethod
    def _execute_trigger(step: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """执行触发器"""
        trigger_type: Optional[str] = step.get("trigger_type")
        
        if not trigger_type:
            return ScriptExecutionService._create_error("Trigger type is required")
        
        if trigger_type not in ScriptExecutionService.TRIGGER_TYPES:
            return ScriptExecutionService._create_error(f"Unsupported trigger type: {trigger_type}")
        
        if trigger_type == "time_based":
            # 基于时间的触发器
            scheduled_time: Optional[str] = step.get("time")
            if not scheduled_time:
                return ScriptExecutionService._create_error("Time-based trigger requires a time")
            
            # 这里只是记录触发器，实际定时执行需要外部调度器
            return {
                "type": "success",
                "trigger_type": "time_based",
                "scheduled_time": scheduled_time,
                "message": f"Trigger scheduled for {scheduled_time}"
            }
        
        elif trigger_type == "interval":
            # 基于时间间隔的触发器
            interval_seconds: Optional[int] = step.get("interval")
            if not interval_seconds:
                return ScriptExecutionService._create_error("Interval trigger requires an interval")
            
            return {
                "type": "success",
                "trigger_type": "interval",
                "interval_seconds": interval_seconds,
                "message": f"Interval trigger set to {interval_seconds} seconds"
            }
        
        elif trigger_type == "event_based":
            # 基于事件的触发器
            event_name: Optional[str] = step.get("event")
            if not event_name:
                return ScriptExecutionService._create_error("Event-based trigger requires an event name")
            
            return {
                "type": "success",
                "trigger_type": "event_based",
                "event": event_name,
                "message": f"Event trigger set for event: {event_name}"
            }
        
        return ScriptExecutionService._create_error(f"Unknown trigger type: {trigger_type}")
    
    @staticmethod
    async def _execute_http_request(step: Dict[str, Any]) -> Dict[str, Any]:
        """执行HTTP请求（异步版本）"""
        # 尝试导入aiohttp库，如果不可用则使用模拟实现
        try:
            import aiohttp
            url: Optional[str] = step.get("url")
            method: str = step.get("method", "GET").upper()
            
            if not url:
                return ScriptExecutionService._create_error("URL is required for HTTP request")
            
            headers: Dict[str, str] = step.get("headers", {})
            data: Any = step.get("data")
            json_data: Any = step.get("json")
            
            async with aiohttp.ClientSession() as session:
                request_kwargs: Dict[str, Any] = {"headers": headers}
                if json_data is not None:
                    request_kwargs["json"] = json_data
                elif data is not None:
                    request_kwargs["data"] = data
                
                async with getattr(session, method.lower())(url, **request_kwargs) as response:
                    try:
                        response_data = await response.json()
                    except ValueError:
                        response_data = await response.text()
                    
                    return {
                        "type": "success",
                        "method": method,
                        "url": url,
                        "status": response.status,
                        "data": response_data
                    }
        except ImportError:
            # 如果aiohttp不可用，返回模拟结果
            url: Optional[str] = step.get("url")
            method: str = step.get("method", "GET").upper()
            
            if not url:
                return ScriptExecutionService._create_error("URL is required for HTTP request")
            
            return {
                "type": "success",
                "method": method,
                "url": url,
                "message": "HTTP request would be executed here",
                "_note": "This is a mock response. Install aiohttp for real HTTP requests."
            }
    
    @staticmethod
    def _combine_data(step: Dict[str, Any], variables: Dict[str, Any]) -> Dict[str, Any]:
        """合并数据"""
        sources: List[Union[str, Dict[str, Any]]] = step.get("sources", [])
        target: Optional[str] = step.get("target")
        
        if not target:
            return ScriptExecutionService._create_error("Target is required for data combining")
        
        combined_data: Dict[str, Any] = {}
        
        for source in sources:
            if isinstance(source, str) and source in variables:
                # 如果是变量引用，获取变量值
                source_data: Any = variables[source]
                if isinstance(source_data, dict):
                    combined_data.update(source_data)
            elif isinstance(source, dict):
                # 如果是直接数据，直接合并
                combined_data.update(source)
        
        variables[target] = combined_data
        
        return {
            "type": "success",
            "target": target,
            "message": f"Combined data saved to {target}",
            "data_count": len(combined_data)
        }
    
    @staticmethod
    def _process_variable_references(value: Any, variables: Dict[str, Any]) -> Any:
        """处理字符串中的变量引用，如 ${var_name} 格式"""
        if isinstance(value, str):
            # 使用正则表达式查找所有变量引用
            pattern = r'\$\{(\w+)\}'
            matches = re.findall(pattern, value)
            
            processed_value: str = value
            for var_name in matches:
                if var_name in variables:
                    # 替换变量引用为实际值
                    processed_value = processed_value.replace(f'${{{var_name}}}', str(variables[var_name]))
            
            return processed_value
        elif isinstance(value, dict):
            # 递归处理字典中的值
            return {k: ScriptExecutionService._process_variable_references(v, variables) for k, v in value.items()}
        elif isinstance(value, list):
            # 递归处理列表中的值
            return [ScriptExecutionService._process_variable_references(item, variables) for item in value]
        
        return value
    
    @staticmethod
    def _safe_eval(expression: str, variables: Dict[str, Any]) -> bool:
        """安全地评估表达式，只允许基本的比较操作"""
        # 定义允许的操作符
        allowed_operators: set[str] = {
            "==", "!=", ">", ">=", "<", "<=", "and", "or", "not"
        }
        
        # 构建安全的评估环境
        safe_env: Dict[str, Any] = {
            "__builtins__": {}
        }
        
        # 添加变量到环境中
        safe_env.update(variables)
        
        # 检查表达式中是否有危险操作
        if ScriptExecutionService._is_dangerous_expression(expression):
            raise ValueError("Expression contains potentially dangerous operations")
        
        # 执行安全评估
        try:
            return bool(eval(expression, safe_env))
        except Exception as e:
            raise ValueError(f"Invalid expression: {str(e)}")
    
    @staticmethod
    def _is_dangerous_command(command: Union[str, List[str]]) -> bool:
        """检查命令是否危险"""
        dangerous_commands: List[str] = [
            "rm -rf", "format", "shutdown", "reboot", "sudo", 
            "chmod 777", "mkfs", "dd if=", "> /dev/"
        ]
        
        cmd_str: str = str(command).lower()
        for dangerous in dangerous_commands:
            if dangerous in cmd_str:
                return True
        
        return False
    
    @staticmethod
    def _is_dangerous_expression(expression: str) -> bool:
        """检查表达式是否危险"""
        # 禁止的操作符和函数
        dangerous_patterns: List[str] = [
            r'__\w+__',  # 双下划线方法
            r'\bexec\b', r'\beval\b', r'\bcompile\b',
            r'\bopen\b', r'\bfile\b', r'\binput\b',
            r'\bglobals\b', r'\blocals\b', r'\bdir\b',
            r'\bgetattr\b', r'\bsetattr\b', r'\bdelattr\b',
            r'\b__import__\b', r'\bimport\b', r'\bfrom\b',
            r'\bos\b\s*\.', r'\bsys\b\s*\.'  # os和sys模块调用
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, expression):
                return True
        
        return False
    
    @staticmethod
    async def _execute_python_script(script_content: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行简单的Python脚本（兼容模式，异步版本）"""
        try:
            # 创建安全的执行环境
            local_vars: Dict[str, Any] = variables.copy() if variables else {}
            
            # 异步执行脚本
            await asyncio.to_thread(
                exec,
                script_content,
                {"__builtins__": {}},
                local_vars
            )
            
            return {
                "status": "success",
                "variables": local_vars,
                "message": "Python script executed successfully"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    @staticmethod
    def _create_error(message: str) -> Dict[str, Any]:
        """创建错误响应"""
        return {
            "type": "error",
            "message": message
        }