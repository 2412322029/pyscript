import asyncio
from pprint import pprint

from script_execution_service import ScriptExecutionService


async def run_all_tests():
    test_script_2 = {
        "steps": [
            {"action": "set_var", "name": "api_key", "value": "123"},
            {"action": "set_var", "name": "b", "value": "123"},
            {
                "action": "condition",
                "condition": "${api_key} + ${b} == 246",
                "if_true": [
                    {"action": "print_msg", "message": "${api_key} + ${b} == 246"}
                ],
                "if_false": [
                    {"action": "print_msg", "message": "${api_key} + ${b} != 246"}
                ],
            },
            {"action": "set_var", "name": "i", "value": 0},
            {
                "action": "loop",
                "condition": "${i} < 4",
                "loop_steps": [
                    {"action": "delay", "seconds": "${i}", "eval": True},
                    {
                        "action": "set_var",
                        "name": "i",
                        "value": "${i} + 1",
                        "eval": True,
                    },
                    {"action": "print_msg", "message": "i=${i}"},
                ],
            },
            {
                "action": "http_request",
                "url": "https://httpbin.org/get",
                "method": "GET",
                "headers": {
                    "X-Custom-Header": "TestValue",
                    "Api-key": "${api_key}",
                    "X-Test-Id": "12345",
                    "User-Agent": "CustomTestAgent/1.0",
                },
                "body": {"key": "value"},
                "params": {"key": "value"},
                "cookies": {"key": "value"},
                "timeout": 10,
                "verify_ssl": True,
                "data": {"key": "value"},
            },
            {"action": "set_var", "name": "response", "value": "${response}"},
        ]
    }
    # 初始化脚本执行服务
    S = ScriptExecutionService(log_level="DEBUG")

    # 打印元数据
    pprint(S.get_supported_actions_metadata())

    # 测试脚本执行服务
    result = await S.execute_script(
        script_content="print('hello world')", script_content_type="python"
    )
    pprint(result)

    # 创建任务
    status_task = asyncio.create_task(
        S.flush_print_queue(lambda msg: print(f"{S.status}: {msg}", end=""), timeout=30)
    )
    script_task = asyncio.create_task(
        S.execute_script(
            script_content=test_script_2, script_content_type="json", log_history=True
        )
    )
    # 等待所有任务完成
    await asyncio.gather(script_task, status_task)

    pprint(S.context())


if __name__ == "__main__":
    asyncio.run(run_all_tests())
