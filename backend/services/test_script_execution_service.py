import asyncio
from pprint import pprint

from script_execution_service import ScriptExecutionService

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
async def run_all_tests():
    
    # 初始化脚本执行服务
    S = ScriptExecutionService(log_level="DEBUG")

    # 打印元数据
    print("支持的操作元数据:")
    pprint(S.get_supported_actions_metadata())
    print("-" * 20)

    # 测试脚本执行服务
    await S.execute_script(
        script_content="print('hello world');eval('print(\"hello eval\")')",
        script_content_type="python",
    )

    # 添加观察者
    def status_changed(new_value):
        print(f"status changed to {new_value}")

    S.add_status_observer(status_changed)
    # 创建任务
    status_task = asyncio.create_task(
        S.flush_print_queue(
            lambda msg: print(
                f"打印任务 status {S.status}: {msg} 执行上下文={S.get_context().model_dump(mode='python')}"
            ),
            timeout=20,
        )
    )
    script_task = asyncio.create_task(
        S.execute_script(
            script_content=test_script_2, script_content_type="json", log_history=True
        )
    )
    # 等待所有任务完成
    await asyncio.gather(script_task, status_task)

    # 先后执行相同脚本
    # await S.execute_script(
    #     script_content="print('hello world');eval('print(\"hello eval\")')", script_content_type="python"
    # )
    # await S.flush_print_queue(lambda msg: print(f"{S.status}: {msg}", end=""), timeout=30)


if __name__ == "__main__":
    asyncio.run(run_all_tests())
    
    # 将 test_script_2 字典转为字符串后，把双引号转义为 \"
    # print(json.dumps(test_script_2, ensure_ascii=False).replace("\"", "\\\""))
