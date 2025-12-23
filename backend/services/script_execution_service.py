import asyncio
import inspect
import logging
import re
import subprocess
from datetime import datetime
from traceback import format_exc
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# 定义泛型类型变量
T = TypeVar("T")


def action_register(
    name: str,
    description: str,
    required_options: List[str] = None,
    optional_options: List[str] = None,
    options_schema: Dict[str, Any] = None,
):
    """动作注册装饰器，用于自动将动作方法注册到ScriptExecutionService.SUPPORTED_ACTIONS中
    Args:
        name: 动作名称
        description: 动作描述
        required_options: 必需参数列表
        optional_options: 可选参数列表
        options_schema: 参数验证模式
    Returns:
        装饰器函数
    """

    def decorator(
        func: Callable[..., Dict[str, Any]],
    ) -> Callable[..., Dict[str, Any]]:
        # 自动从函数签名中提取参数信息，如果没有手动提供
        if required_options is None and optional_options is None:
            sig = inspect.signature(func)
            # 排除第一个参数(self)和context相关参数
            params = list(sig.parameters.keys())[1:]
            # 简单处理：假设前两个参数是必需的（step和variables），其余是可选的
            req_opts = params[:2] if len(params) >= 2 else params
            opt_opts = params[2:] if len(params) > 2 else []
        else:
            req_opts = required_options or []
            opt_opts = optional_options or []
        # 如果没有提供options_schema，则自动生成基础的schema
        if options_schema is None:
            auto_schema = {}
            for opt in req_opts + opt_opts:
                # 默认类型设置为string，实际使用时可能需要根据参数名或类型提示进一步补充
                auto_schema[opt] = {"type": "string", "description": f"参数 {opt}"}
            schema = auto_schema
        else:
            schema = options_schema
        # 注册动作到SUPPORTED_ACTIONS字典
        SUPPORTED_ACTIONS[name] = {
            "description": description,
            "func": func,
            "required_options": req_opts,
            "optional_options": opt_opts,
            "options_schema": schema,
        }
        # 返回原始函数
        return func

    return decorator


SUPPORTED_ACTIONS: Dict[str, Dict[str, Any]] = {}


class ScriptExecutionService:
    """脚本执行服务类，负责解析和执行JSON格式的脚本
    异步实现，适配FastAPI框架，支持各种脚本操作
    """

    global_context: Dict[str, Any] = {}
    # 类级别的支持动作字典

    def __init__(self, log_level=logging.INFO):
        """初始化脚本执行服务"""
        self.context: Dict[str, Any] = {
            "status": "created",
            "results_msg": {},
            "print_msg": "",
            "variables": {},
            "execution_history": [],
            "start_time": datetime.now().isoformat(),
            "execution_time": None,
        }

    # 触发器类型
    TRIGGER_TYPES: set[str] = {"time_based", "interval", "event_based"}

    async def execute_script(
        self,
        script_content: Dict[str, Any],
        variables: Dict[str, Any] = None,
        log_history: bool = False,
        script_content_type: str = "json",
    ) -> Dict[str, Any]:
        """执行脚本"""
        # 验证脚本格式
        if isinstance(script_content, str):
            return await self._execute_python_script(script_content)
        # 初始化执行上下文
        self.context["variables"].update(variables or {})
        # 获取步骤列表
        steps = script_content.get("steps", []) 
        # 执行步骤
        for i, step in enumerate(steps):
            logger.debug("Step details: %s", step)
            result = await self._execute_step(step, self.context, log_history)
            if result["sub_result"] != "success":
                self.context["status"] = "error"
                logger.error(
                    "Step %d failed: %s", i + 1, result.get("message", "Unknown error")
                )
                return {
                    "result": "error",
                    "message": f"Step {i + 1} failed: {result.get('message', 'Unknown error')}",
                }
        # 执行完成
        self.context["status"] = "completed"
        return {
            "result": "success",
            "message": f"Script executed successfully with {len(steps)} steps",
        }

    async def _execute_step(
        self,
        step: Dict[str, Any],
        context: Dict[str, Any],
        log_history: bool = True,
    ) -> Dict[str, Any]:
        """执行单个脚本步骤（异步版本）"""
        action_type: Optional[str] = step.get("action")
        if not action_type:
            return self._create_error("Action type is required")
        # 检查动作类型是否支持（现在检查字典的键）
        if action_type not in SUPPORTED_ACTIONS:
            return self._create_error(f"Unsupported action type: {action_type}")
        timestamp: str = datetime.now().isoformat()
        try:
            # 验证必需参数
            action_metadata = SUPPORTED_ACTIONS[action_type]
            required_options = action_metadata.get("required_options", [])
            for option in required_options:
                if option not in step:
                    return self._create_error(
                        f"Missing required option '{option}' for action '{action_type}'"
                    )
            # 获取注册的动作函数
            action_func = action_metadata.get("func")
            # 根据函数签名传递正确的参数
            sig = inspect.signature(action_func)
            params = list(sig.parameters.keys())
            # 准备参数
            args = []
            if "step" in params:
                args.append(step)
            if "variables" in params:
                args.append(context["variables"])
            if "context" in params:
                args.append(context)
            if "log_history" in params:
                args.append(log_history)
            # 执行动作函数
            if asyncio.iscoroutinefunction(action_func):
                result = await action_func(*args)
            else:
                result = action_func(*args)
            # 记录执行历史
            if log_history:
                context["execution_history"].append(
                    {"timestamp": timestamp, "action": action_type, "result": result}
                )
            return result
        except Exception as e:
            error_message = f"Error executing {action_type}: {str(e)}"
            return self._create_error(error_message, tb=format_exc())

    def get_supported_actions_metadata(self) -> Dict[str, Dict[str, Any]]:
        """获取支持的动作元数据，供前端使用
        Returns:
            包含所有支持动作元数据的字典
        """
        # 返回SUPPORTED_ACTIONS的副本，不包含func字段
        metadata = {}
        for action_name, action_data in self.SUPPORTED_ACTIONS.items():
            metadata[action_name] = {
                k: v for k, v in action_data.items() if k != "func"
            }
        return metadata

    @action_register(
        name="set_var",
        description="设置变量值",
        required_options=["name", "value"],
        options_schema={
            "name": {"type": "string", "description": "变量名称"},
            "value": {"type": "any", "description": "变量值"},
        },
    )
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
            "sub_result": "success",
            "message": f"Variable '{var_name}' set to '{processed_value}'",
        }

    @action_register(
        name="print_msg",
        description="打印消息",
        required_options=["message"],
        options_schema={"message": {"type": "string", "description": "要打印的消息"}},
    )
    def _print(self, step: Dict[str, Any], variables: Dict[str, Any]) -> Dict[str, Any]:
        """打印消息"""
        message: Optional[str] = step.get("message")
        message = self._process_variable_references(message, variables)
        if not message:
            return self._create_error("Message is required")
        self.context["print_msg"] += f"{message}\n"
        return {"sub_result": "success", "message": "Printed msg"}

    @action_register(
        name="execute_command",
        description="执行系统命令",
        required_options=["command"],
        optional_options=["shell", "timeout"],
        options_schema={
            "command": {"type": "string|list", "description": "要执行的命令"},
            "shell": {"type": "boolean", "description": "是否通过shell执行"},
            "timeout": {"type": "number", "description": "超时时间（秒）"},
        },
    )
    async def _execute_command(
        self, step: Dict[str, Any], context: Dict[str, Any], log_history: bool = True
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
            context["print_msg"] += f"stdout: {result.stdout}\n"
            context["print_msg"] += f"stderr: {result.stderr}\n"
            context["variables"]["exit_code"] = result.returncode
            context["variables"]["stdout"] = result.stdout
            context["variables"]["stderr"] = result.stderr
            return {
                "sub_result": "success",
                "message": f"Command executed with exit code {result.returncode}",
            }
        except subprocess.TimeoutExpired:
            return self._create_error("Command execution timed out")
        except Exception as e:
            return self._create_error(f"Command execution failed: {str(e)}")

    @action_register(
        name="condition",
        description="条件判断",
        required_options=["condition", "if_steps", "else_steps"],
        options_schema={
            "condition": {"type": "string", "description": "条件表达式"},
            "if_steps": {"type": "array", "description": "条件为真时执行的步骤"},
            "else_steps": {"type": "array", "description": "条件为假时执行的步骤"},
        },
    )
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
                "sub_result": "success",
                "message": f"Condition result: {result}",
            }
        except Exception as e:
            return ScriptExecutionService._create_error(
                f"Condition evaluation failed: {str(e)}"
            )

    @action_register(
        name="loop",
        description="循环执行",
        required_options=["times", "steps"],
        options_schema={
            "times": {"type": "number", "description": "循环次数"},
            "steps": {"type": "array", "description": "循环执行的步骤"},
        },
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
            return {
                "sub_result": "success",
                "message": f"Executed {iteration_count} iterations",
            }
        except Exception as e:
            return self._create_error(f"Loop execution failed: {str(e)}")

    @action_register(
        name="delay",
        description="延时等待",
        required_options=["seconds"],
        options_schema={"seconds": {"type": "number", "description": "延时秒数"}},
    )
    async def _execute_delay(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """执行延迟（异步版本）"""
        delay_seconds: Union[int, float] = step.get("seconds", 1)
        try:
            # 使用异步sleep代替同步sleep
            await asyncio.sleep(float(delay_seconds))
            return {
                "sub_result": "success",
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
        return {
            "sub_result": "success",
            "message": f"Logged: {processed_message} level: {level}",
        }

    @action_register(
        name="trigger",
        description="设置触发器",
        required_options=["type", "steps"],
        optional_options=["config"],
        options_schema={
            "type": {
                "type": "string",
                "description": "触发器类型",
                "enum": ["time_based", "interval", "event_based"],
            },
            "steps": {"type": "array", "description": "触发时执行的步骤"},
            "config": {"type": "object", "description": "触发器配置"},
        },
    )
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
                "sub_result": "success",
                "message": f"Trigger time_based scheduled for {scheduled_time}",
            }
        elif trigger_type == "interval":
            # 基于时间间隔的触发器
            interval_seconds: Optional[int] = step.get("interval")
            if not interval_seconds:
                return self._create_error("Interval trigger requires an interval")
            return {
                "sub_result": "success",
                "message": f"Interval trigger set to {interval_seconds} seconds",
            }
        elif trigger_type == "event_based":
            # 基于事件的触发器
            event_name: Optional[str] = step.get("event")
            if not event_name:
                return self._create_error("Event-based trigger requires an event name")
            return {
                "sub_result": "success",
                "message": f"Event trigger set for event: {event_name}",
            }
        return self._create_error(f"Unknown trigger type: {trigger_type}")

    @action_register(
        name="http_request",
        description="执行HTTP请求",
        options_schema={
            "url": {"type": "string", "required": True, "description": "请求URL"},
            "method": {
                "type": "string",
                "default": "GET",
                "enum": ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"],
                "description": "HTTP方法",
            },
            "headers": {"type": "object", "description": "HTTP请求头"},
            "params": {"type": "object", "description": "URL查询参数"},
            "cookies": {"type": "object", "description": "Cookies"},
            "proxy": {"type": "string", "description": "代理URL"},
            "content_type": {"type": "string", "description": "Content-Type"},
            "data": {"type": "any", "description": "请求体数据"},
            "json": {"type": "object", "description": "JSON请求体"},
            "timeout": {"type": "number", "description": "超时时间（秒）"},
            "allow_redirects": {
                "type": "boolean",
                "default": True,
                "description": "是否允许重定向",
            },
            "verify_ssl": {
                "type": "boolean",
                "default": True,
                "description": "是否验证SSL证书",
            },
            "return_json": {
                "type": "boolean",
                "default": False,
                "description": "是否返回JSON格式",
            },
            "return_var": {"type": "string", "description": "结果存储的变量名"},
            "return_format": {
                "type": "string",
                "enum": ["json", "text", "dict"],
                "description": "返回数据格式",
            },
        },
        optional_options=[
            "headers",
            "params",
            "cookies",
            "proxy",
            "content_type",
            "data",
            "json",
            "timeout",
            "allow_redirects",
            "verify_ssl",
            "return_json",
            "return_var",
            "return_format",
        ],
    )
    async def _execute_http_request(
        self, step: Dict[str, Any], context: Dict[str, Any], log_history: bool
    ) -> Dict[str, Any]:
        """执行HTTP请求（异步版本）"""
        try:
            from traceback import format_exc

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
                        value, context["variables"]
                    )
                else:
                    result_params[key] = None
            # 设置Content-Type头（如果提供）
            if result_params["content_type"] is not None:
                if result_params["headers"] is None:
                    result_params["headers"] = {}
                result_params["headers"]["Content-Type"] = result_params["content_type"]
            # 其他配置参数
            timeout_seconds = step.get("timeout")
            allow_redirects = step.get("allow_redirects", True)
            verify_ssl = step.get("verify_ssl", True)
            return_json = step.get("return_json", False)
            # 获取返回变量名和格式
            return_var = step.get("return_var", "response")  # 默认存储在response变量
            # 验证return_var参数
            import re

            if not isinstance(return_var, str):
                return self._create_error("return_var must be a string")
            # 检查变量名是否有效（只允许字母、数字和下划线）
            if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", return_var):
                return self._create_error(
                    f"Invalid variable name: {return_var}. Only letters, numbers and underscores allowed, and must start with a letter or underscore"
                )
            # 检查是否是保留变量名
            reserved_vars = ["response", "status", "response_headers"]
            if return_var in reserved_vars and return_var != "response":
                return self._create_error(
                    f"Cannot use reserved variable name: {return_var}"
                )
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
                    context["variables"][return_var] = response_data
                    context["variables"]["response"] = response_data
                    context["variables"]["status"] = response.status
                    context["variables"]["response_headers"] = dict(response.headers)
                    return {
                        "sub_result": "success",
                        "message": f"HTTP request {method} {result_params['url']} status: {response.status}",
                    }
        except ImportError:
            return self._create_error("aiohttp library is required for HTTP requests.")
        except Exception as e:
            return self._create_error(
                f"Error executing HTTP request: {str(e)}", tb=format_exc()
            )

    @action_register(
        name="combine_data",
        description="合并数据",
        required_options=["data_sources"],
        optional_options=["output_var"],
        options_schema={
            "data_sources": {"type": "array", "description": "数据源列表"},
            "output_var": {"type": "string", "description": "输出变量名"},
        },
    )
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
            "sub_result": "success",
            "message": f"Combined data saved to {target}",
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
                "print": print,
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
                "list": list,
                "dict": dict,
                "len": len,
                "range": range,
                "abs": abs,
                "min": min,
                "max": max,
            }
            # 异步执行脚本
            await asyncio.to_thread(
                exec, script_content, {"__builtins__": safe_builtins}, local_vars
            )
            return {
                "status": "success",
                "message": "Python script executed successfully",
            }
        except Exception:
            logger.error(f"Python脚本执行错误: {format_exc()}")
            return {"status": "error", "error": format_exc()}

    def _create_error(self, message: str, tb: str = "") -> Dict[str, Any]:
        """创建错误响应"""
        if tb:
            self.context["print_msg"] += f"\n{tb}"
        caller_name = inspect.stack()[1].function
        return {
            "sub_result": "error",
            "message": f"[func: {caller_name}] {message}",
            "traceback": tb,
        }
