import asyncio
import json
import logging
import re
import subprocess
from datetime import datetime
from traceback import format_exc
from typing import Any, Dict, List, Optional, Union

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ScriptExecutionService:
    """脚本执行服务类，负责解析和执行JSON格式的脚本

    异步实现，适配FastAPI框架，支持各种脚本操作
    """

    global_context: Dict[str, Any] = {}

    def __init__(self):
        self.context: Dict[str, Any] = {
            "status": "created",
            "results_msg": {},
            "print_msg": "",
            "execution_history": [],
            "start_time": datetime.now().isoformat(),
            "execution_time": None,
        }

    # 支持的操作类型
    SUPPORTED_ACTIONS: set[str] = {
        "set_var",
        "get_var",
        "execute_command",
        "condition",
        "loop",
        "delay",
        "log",
        "trigger",
        "http_request",
        "combine_data",
    }

    # 触发器类型
    TRIGGER_TYPES: set[str] = {"time_based", "interval", "event_based"}

    async def execute_script(
        self,
        script_content: Union[str, Dict[str, Any]],
        script_content_type: str = "json",
        variables: Optional[Dict[str, Any]] = None,
        log_history: bool = False,
    ) -> Dict[str, Any]:
        """
        执行脚本内容（异步版本）

        Args:
            script_content: 脚本内容(JSON字符串或字典)
            script_content_type: 脚本内容类型，默认"json"，也可以是"python"
            variables: 初始变量字典
            log_history: 是否记录执行历史，默认True

        Returns:
            执行结果字典
        """
        try:
            # 解析脚本内容
            if script_content_type == "json":
                if isinstance(script_content, str):
                    try:
                        script_data: Dict[str, Any] = json.loads(script_content)
                    except json.JSONDecodeError:
                        # 如果不是有效的JSON，尝试作为Python代码执行（简单兼容）
                        return await self._execute_python_script(script_content, variables)
                else:
                    script_data = script_content
            elif script_content_type == "python":
                return await self._execute_python_script(script_content, variables)
            else:
                return self._create_error(f"Unsupported script content type: {script_content_type}")

            # 初始化变量空间
            self.context["variables"] = variables.copy() if variables else {}

            # 执行脚本步骤
            if "steps" in script_data:
                for step in script_data["steps"]:
                    step_result = await self._execute_step(
                        step, self.context, log_history
                    )
                    if step_result.get("type") == "error":
                        # 如果步骤执行出错，中断执行
                        self.context["status"] = "error"
                        self.context["results_msg"] = step_result["message"]
                        break
                    self.context["results_msg"].update(step_result.get("results", {}))
            else:
                # 单步骤执行模式
                step_result = await self._execute_step(
                    script_data, self.context, log_history
                )
                if step_result.get("type") == "error":
                    self.context["status"] = "error"
                    self.context["results_msg"] = step_result["message"]

            # 完成执行
            self.context["end_time"] = datetime.now().isoformat()
            return self.context

        except Exception as e:
            logger.error(f"Script execution failed: {str(e)}")
            return {"status": "error", "results_msg": str(e)}

    async def _execute_step(
        self, step: Dict[str, Any], context: Dict[str, Any], log_history: bool = True
    ) -> Dict[str, Any]:
        """执行单个脚本步骤（异步版本）"""
        action_type: Optional[str] = step.get("action")

        if not action_type:
            return self._create_error("Action type is required")

        if action_type not in self.SUPPORTED_ACTIONS:
            return self._create_error(f"Unsupported action type: {action_type}")

        timestamp: str = datetime.now().isoformat()

        try:
            # 根据动作类型执行相应操作
            if action_type == "set_var":
                result = self._set_variable(step, context["variables"])
            elif action_type == "get_var":
                result = self._get_variable(step, context["variables"])
            elif action_type == "execute_command":
                result = await self._execute_command(step)
            elif action_type == "condition":
                result = await self._execute_condition(step, context, log_history)
            elif action_type == "loop":
                result = await self._execute_loop(step, context, log_history)
            elif action_type == "delay":
                result = await self._execute_delay(step, context, log_history)
            elif action_type == "log":
                result = self._execute_log(step)
            elif action_type == "trigger":
                result = self._execute_trigger(step, context, log_history)
            elif action_type == "http_request":
                result = await self._execute_http_request(step, context["variables"])
            elif action_type == "combine_data":
                result = self._combine_data(step, context["variables"])
            else:
                result = self._create_error(f"Unknown action type: {action_type}")

            # 记录执行历史
            if log_history:
                context["execution_history"].append(
                    {"timestamp": timestamp, "action": action_type, "result": result}
                )

            return result

        except Exception as e:
            error_message = f"Error executing {action_type}: {str(e)}"
            return self._create_error(error_message,tb=format_exc())

    def _set_variable(
        self, step: Dict[str, Any], variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """设置变量"""
        var_name: Optional[str] = step.get("name")
        var_value: Any = step.get("value")

        if not var_name:
            return self._create_error("_set_variable: Variable name is required")

        # 处理变量引用
        processed_value: Any = self._process_variable_references(var_value, variables)

        variables[var_name] = processed_value

        return {
            "type": "success",
            "message": f"Variable '{var_name}' set",
            "value": processed_value,
        }

    def _get_variable(
        self, step: Dict[str, Any], variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """获取变量"""
        var_name: Optional[str] = step.get("name")
        target: Optional[str] = step.get("target")

        if not var_name:
            return self._create_error("_get_variable: Variable name is required")

        if var_name not in variables:
            return self._create_error(f"_get_variable: Variable '{var_name}' not found")

        value: Any = variables[var_name]
        self.context.print_msg += f"Variable '{var_name}' = {value}\n"
        if target:
            return {"type": "success", "target": target, "value": value}

        return {"type": "success", "value": value}

    async def _execute_command(
        self, step: Dict[str, Any], log_history: bool = True
    ) -> Dict[str, Any]:
        """执行命令（异步版本）"""
        command: Optional[Union[str, List[str]]] = step.get("command")
        shell: bool = step.get("shell", False)
        timeout: int = step.get("timeout", 60)

        if not command:
            return self._create_error("_execute_command: Command is required")

        try:
            # 安全检查 - 不允许执行危险命令
            if self._is_dangerous_command(command):
                return self._create_error(
                    "Command execution not allowed for security reasons"
                )

            # 异步执行命令
            result = await asyncio.to_thread(
                subprocess.run,
                command if isinstance(command, list) else command,
                shell=shell,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            return {
                "type": "success",
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }

        except subprocess.TimeoutExpired:
            return self._create_error("Command execution timed out")
        except Exception as e:
            return self._create_error(f"Command execution failed: {str(e)}")

    async def _execute_condition(
        self, step: Dict[str, Any], context: Dict[str, Any], log_history: bool = True
    ) -> Dict[str, Any]:
        """执行条件判断（异步版本）"""
        condition: Optional[str] = step.get("condition")
        if_true: List[Dict[str, Any]] = step.get("if_true", [])
        if_false: List[Dict[str, Any]] = step.get("if_false", [])

        if not condition:
            return self._create_error("_execute_condition:  Condition is required")

        try:
            # 处理变量引用
            processed_condition: str = self._process_variable_references(
                condition, context["variables"]
            )

            # 安全评估条件表达式
            result: bool = self._safe_eval(processed_condition, context["variables"])

            # 根据条件结果执行相应步骤
            steps_to_execute: List[Dict[str, Any]] = if_true if result else if_false

            for sub_step in steps_to_execute:
                sub_result = await self._execute_step(sub_step, context, log_history)
                if sub_result.get("type") == "error":
                    return sub_result

            return {
                "type": "success",
                "condition_result": result,
                "executed": "if_true" if result else "if_false",
            }

        except Exception as e:
            return ScriptExecutionService._create_error(
                f"Condition evaluation failed: {str(e)}"
            )

    async def _execute_loop(
        self, step: Dict[str, Any], context: Dict[str, Any], log_history: bool = True
    ) -> Dict[str, Any]:
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
                        return self._create_error("Loop exceeded maximum iterations")

                    context["variables"]["loop_index"] = i
                    for sub_step in loop_steps:
                        sub_result = await self._execute_step(
                            sub_step, context, log_history
                        )
                        if sub_result.get("type") == "error":
                            return sub_result
                    iteration_count += 1

            elif loop_type == "while":
                if not condition:
                    return self._create_error("While loop requires a condition")

                # 执行条件循环
                while True:
                    if iteration_count >= max_iterations:
                        return self._create_error("Loop exceeded maximum iterations")

                    processed_condition: str = self._process_variable_references(
                        condition, context["variables"]
                    )
                    if not self._safe_eval(processed_condition, context["variables"]):
                        break

                    for sub_step in loop_steps:
                        sub_result = await self._execute_step(
                            sub_step, context, log_history
                        )
                        if sub_result.get("type") == "error":
                            return sub_result
                    iteration_count += 1

            return {"type": "success", "iterations_executed": iteration_count}

        except Exception as e:
            return ScriptExecutionService._create_error(
                f"Loop execution failed: {str(e)}"
            )

    async def _execute_delay(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """执行延迟（异步版本）"""
        delay_seconds: Union[int, float] = step.get("seconds", 1)

        try:
            # 使用异步sleep代替同步sleep
            await asyncio.sleep(float(delay_seconds))
            return {
                "type": "success",
                "message": f"Delayed for {delay_seconds} seconds",
            }
        except ValueError:
            return self._create_error("Invalid delay seconds value")

    def _execute_log(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """执行日志记录"""
        message: str = step.get("message", "")
        level: str = step.get("level", "info")

        # 处理变量引用
        variables: Dict[str, Any] = step.get("variables", {})
        processed_message: str = self._process_variable_references(message, variables)

        # 记录日志
        log_method = getattr(logger, level.lower(), logger.info)
        log_method(processed_message)

        return {"type": "success", "message": processed_message, "level": level}

    def _execute_trigger(
        self, step: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行触发器"""
        trigger_type: Optional[str] = step.get("trigger_type")

        if not trigger_type:
            return self._create_error("Trigger type is required")

        if trigger_type not in self.TRIGGER_TYPES:
            return self._create_error(f"Unsupported trigger type: {trigger_type}")

        if trigger_type == "time_based":
            # 基于时间的触发器
            scheduled_time: Optional[str] = step.get("time")
            if not scheduled_time:
                return self._create_error("Time-based trigger requires a time")

            # 这里只是记录触发器，实际定时执行需要外部调度器
            return {
                "type": "success",
                "trigger_type": "time_based",
                "scheduled_time": scheduled_time,
                "message": f"Trigger scheduled for {scheduled_time}",
            }

        elif trigger_type == "interval":
            # 基于时间间隔的触发器
            interval_seconds: Optional[int] = step.get("interval")
            if not interval_seconds:
                return self._create_error("Interval trigger requires an interval")

            return {
                "type": "success",
                "trigger_type": "interval",
                "interval_seconds": interval_seconds,
                "message": f"Interval trigger set to {interval_seconds} seconds",
            }

        elif trigger_type == "event_based":
            # 基于事件的触发器
            event_name: Optional[str] = step.get("event")
            if not event_name:
                return self._create_error("Event-based trigger requires an event name")

            return {
                "type": "success",
                "trigger_type": "event_based",
                "event": event_name,
                "message": f"Event trigger set for event: {event_name}",
            }

        return self._create_error(f"Unknown trigger type: {trigger_type}")

    async def _execute_http_request(
        self, step: Dict[str, Any], variables: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """执行HTTP请求（异步版本）- 简化版本"""

        try:
            import aiohttp
            # 获取基本参数
            url = step.get("url")
            method = step.get("method", "GET").upper()

            if not url:
                return self._create_error("URL is required for HTTP request")
            # 定义需要处理变量引用的参数映射
            param_mapping = {
                "url": url,
                "headers": step.get("headers", {}),
                "params": step.get("params", {}),
                "cookies": step.get("cookies", {}),
                "proxy_url": step.get("proxy"),
                "content_type": step.get("content_type"),
                "data": step.get("data"),
                "json_data": step.get("json"),
            }

            # 批量处理变量引用
            result_params = {}
            for key, value in param_mapping.items():
                if value is not None:
                    result_params[key] = self._process_variable_references(
                        value, variables
                    )
                else:
                    result_params[key] = None

            # 设置Content-Type头（如果提供）
            if result_params["content_type"] is not None:
                result_params["headers"]["Content-Type"] = result_params["content_type"]

            # 其他配置参数
            timeout_seconds = step.get("timeout")
            allow_redirects = step.get("allow_redirects", True)
            verify_ssl = step.get("verify_ssl", True)
            return_json = step.get("return_json", False)

            # 创建请求超时配置
            timeout = aiohttp.ClientTimeout(
                total=timeout_seconds if timeout_seconds is not None else 10.0
            )

            # 创建代理连接器
            connector = (
                aiohttp.ProxyConnector.from_url(result_params["proxy_url"])
                if result_params["proxy_url"]
                else None
            )

            async with aiohttp.ClientSession(connector=connector) as session:
                # 构建请求参数字典
                request_kwargs = {
                    "headers": result_params["headers"],
                    "params": result_params["params"],
                    "timeout": timeout,
                    "cookies": result_params["cookies"],
                    "allow_redirects": allow_redirects,
                    "verify_ssl": verify_ssl,
                }

                # 根据数据类型设置相应的请求体
                if result_params["json_data"] is not None:
                    request_kwargs["json"] = result_params["json_data"]
                elif result_params["data"] is not None:
                    request_kwargs["data"] = result_params["data"]

                # 执行请求并处理响应
                async with session.request(
                    method, result_params["url"], **request_kwargs
                ) as response:
                    response_content_type = response.headers.get("Content-Type", "")

                    # 处理响应数据
                    if return_json or "application/json" in response_content_type:
                        try:
                            response_data = await response.json()
                        except Exception as e:
                            return ScriptExecutionService._create_error(
                                f"Failed to parse JSON response: {str(e)}"
                            )
                    else:
                        response_data = await response.text()
                    variables["response"] = response_data
                    variables["status"] = response.status
                    variables["response_headers"] = dict(response.headers)
                    return {
                        "type": "success",
                        "method": method,
                        "url": result_params["url"],
                        "status": response.status,
                    }

        except ImportError:
            return self._create_error("aiohttp library is required for HTTP requests.")
        except Exception as e:
            return self._create_error(f"Error executing HTTP request: {str(e)}", tb=format_exc())

    def _combine_data(
        self, step: Dict[str, Any], variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """合并数据"""
        sources: List[Union[str, Dict[str, Any]]] = step.get("sources", [])
        target: Optional[str] = step.get("target")

        if not target:
            return self._create_error("Target is required for data combining")

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
            "data_count": len(combined_data),
        }

    def _process_variable_references(
        self, value: Any, variables: Dict[str, Any]
    ) -> Any:
        """处理字符串中的变量引用，如 ${var_name} 格式"""
        if isinstance(value, str):
            # 使用正则表达式查找所有变量引用
            pattern = r"\$\{(\w+)\}"
            matches = re.findall(pattern, value)

            processed_value: str = value
            for var_name in matches:
                if var_name in variables:
                    # 替换变量引用为实际值
                    processed_value = processed_value.replace(
                        f"${{{var_name}}}", str(variables[var_name])
                    )
                else:
                    # 如果变量不存在，保留原始字符串
                    processed_value = processed_value.replace(
                        f"${{{var_name}}}", f"${{{var_name}}}"
                    )

            return processed_value
        elif isinstance(value, dict):
            # 递归处理字典中的值
            return {
                k: self._process_variable_references(v, variables)
                for k, v in value.items()
            }
        elif isinstance(value, list):
            # 递归处理列表中的值
            return [
                self._process_variable_references(item, variables) for item in value
            ]

        return value

    def _safe_eval(self, expression: str, variables: Dict[str, Any]) -> bool:
        """安全地评估表达式，只允许基本的比较操作"""
        # 定义允许的操作符
        # allowed_operators: set[str] = {
        #     "==",
        #     "!=",
        #     ">",
        #     ">=",
        #     "<",
        #     "<=",
        #     "and",
        #     "or",
        #     "not",
        # }

        # 构建安全的评估环境
        safe_env: Dict[str, Any] = {"__builtins__": {}}

        # 添加变量到环境中
        safe_env.update(variables)

        # 检查表达式中是否有危险操作
        if self._is_dangerous_expression(expression):
            raise ValueError("Expression contains potentially dangerous operations")

        # 执行安全评估
        try:
            return bool(eval(expression, safe_env))
        except Exception as e:
            raise ValueError(f"Invalid expression _safe_eval: {str(e)}")

    def _is_dangerous_command(self, command: Union[str, List[str]]) -> bool:
        """检查命令是否危险"""
        dangerous_commands: List[str] = [
            "rm -rf",
            "format",
            "shutdown",
            "reboot",
            "sudo",
            "chmod 777",
            "mkfs",
            "dd if=",
            "> /dev/",
        ]

        cmd_str: str = str(command).lower()
        for dangerous in dangerous_commands:
            if dangerous in cmd_str:
                return True

        return False

    def _is_dangerous_expression(self, expression: str) -> bool:
        """检查表达式是否危险"""
        # 禁止的操作符和函数
        dangerous_patterns: List[str] = [
            r"__\w+__",  # 双下划线方法
            r"\bexec\b",
            r"\beval\b",
            r"\bcompile\b",
            r"\bopen\b",
            r"\bfile\b",
            r"\binput\b",
            r"\bglobals\b",
            r"\blocals\b",
            r"\bdir\b",
            r"\bgetattr\b",
            r"\bsetattr\b",
            r"\bdelattr\b",
            r"\b__import__\b",
            r"\bimport\b",
            r"\bfrom\b",
            r"\bos\b\s*\.",
            r"\bsys\b\s*\.",  # os和sys模块调用
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, expression):
                return True

        return False

    async def _execute_python_script(
        self, script_content: str, variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """执行简单的Python脚本（兼容模式，异步版本）"""
        try:
            # 创建安全的执行环境
            local_vars: Dict[str, Any] = variables.copy() if variables else {}
            
            # 添加必要的内置函数到__builtins__字典中
            safe_builtins = {
                'print': print,
                'str': str,
                'int': int,
                'float': float,
                'bool': bool,
                'list': list,
                'dict': dict,
                'len': len,
                'range': range,
                'abs': abs,
                'min': min,
                'max': max,
            }

            # 异步执行脚本
            await asyncio.to_thread(
                exec, script_content, {"__builtins__": safe_builtins}, local_vars
            )

            return {
                "status": "success",
                "variables": local_vars,
                "message": "Python script executed successfully",
            }
        except Exception:
            logger.error(f"Python脚本执行错误: {format_exc()}")
            return {"status": "error", "error": format_exc()}

    def _create_error(self, message: str,tb:str="") -> Dict[str, Any]:
        """创建错误响应"""
        if tb:
            self.context["print_msg"] += f"\nTraceback:\n{tb}"
        return {"type": "error", "message": message,"traceback":tb}