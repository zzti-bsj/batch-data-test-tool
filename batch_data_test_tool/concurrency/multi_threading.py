from concurrent.futures import ThreadPoolExecutor
def multi_exec(func, kwargs: dict, max_workers: int = 4):
    """
    :param max_workers: 最大并发数
    :param func: 函数
    :param kwargs: 参数, 参数是一个字典，key是索引，value是参数列表
    :return: 结果, 结果是一个字典，key是索引，value是结果
    线程池执行
    """
    results = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {index: executor.submit(func, **args) for index, args in kwargs.items()}
        for index, future in futures.items():
            results[index] = future.result()
        return results