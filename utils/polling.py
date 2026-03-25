import time

def wait_until(
        func,
        timeout=60,
        interval=3,
        success_condition=lambda x: x,
):
    """
    通用轮询工具

    func: 请求函数
    success_condition: 成功条件
    """
    start = time.time()

    while True:
        result = func()
        if success_condition(result):
            return result
        if time.time() - start > timeout:
            raise TimeoutError("等待任务超时")
        time.sleep(interval)