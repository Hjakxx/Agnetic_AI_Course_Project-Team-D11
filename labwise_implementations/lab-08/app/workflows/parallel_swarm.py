
from concurrent.futures import ThreadPoolExecutor, as_completed
from time import sleep

from app.runtime.agent_runtime import agent_runtime, is_transient_agent_error


def _run_task(task, retry_transient):
    name = task["agent"]
    kwargs = task.get("kwargs", {})
    delays = (0.25, 0.5, 1.0) if retry_transient else ()
    for attempt in range(1, len(delays) + 2):
        try:
            result = agent_runtime.execute_agent(name, **kwargs)
        except Exception as error:
            result = {"status": "error", "message": str(error),
                      "retryable": is_transient_agent_error(error)}

        if not isinstance(result, dict) or result.get("status") != "error":
            return {"agent": name, "status": "success", "result": result, "attempts": attempt}
        if result.get("retryable") is not True or attempt > len(delays):
            return {"agent": name, "status": "error", "attempts": attempt,
                    "message": result.get("message", "Agent execution failed.")}
        sleep(delays[attempt - 1])


def run_parallel_swarm(agent_tasks, max_workers=None, *, retry_transient=False):
    """
    Execute multiple registered agents concurrently,
    collect their results and handle individual failures.
    Enable retry_transient for batches of tasks that are safe to repeat.
    
    Each task must contain:
        {
            "agent": "agent_name",
            "kwargs": {"key": "value"}
        }
    """

    if not isinstance(agent_tasks, list) or not agent_tasks:
        return {
            "status": "error",
            "message": "At least one agent task is required."
        }

    for task in agent_tasks:
        if (
            not isinstance(task, dict)
            or not isinstance(task.get("agent"), str)
            or not task["agent"].strip()
            or not isinstance(task.get("kwargs", {}), dict)
        ):
            return {
                "status": "error",
                "message": "Each task must contain a valid agent name and kwargs dictionary."
            }

    if max_workers is not None and (
        not isinstance(max_workers, int)
        or isinstance(max_workers, bool)
        or max_workers < 1
    ):
        return {
            "status": "error",
            "message": "max_workers must be a positive integer."
        }

    results = [None] * len(agent_tasks)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:

        future_to_index = {
            executor.submit(_run_task, task, retry_transient): index
            for index, task in enumerate(agent_tasks)
        }

        for future in as_completed(future_to_index):
            index = future_to_index[future]
            results[index] = future.result()

    successful_results = [
        item for item in results
        if item["status"] == "success"
    ]

    failed_results = [
        item for item in results
        if item["status"] == "error"
    ]

    if not failed_results:
        status = "success"
    elif successful_results:
        status = "partial_success"
    else:
        status = "error"

    return {
        "status": status,
        "total_agents": len(agent_tasks),
        "successful_agents": len(successful_results),
        "failed_agents": len(failed_results),
        "results": results,
        "merged_result": [
            item["result"] for item in successful_results
        ],
        "errors": failed_results
    }
