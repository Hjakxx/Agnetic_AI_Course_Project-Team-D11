
import time
from unittest.mock import Mock

import pytest
from pymongo.errors import ConfigurationError, NetworkTimeout

from app.agents.coordinator_agent import CoordinatorAgent
from app.workflows.parallel_swarm import run_parallel_swarm


def test_parallel_execution(monkeypatch):
    from app.workflows import parallel_swarm

    def mock_execute_agent(name, **kwargs):
        time.sleep(0.1)
        return {"agent_output": name}

    monkeypatch.setattr(
        parallel_swarm.agent_runtime,
        "execute_agent",
        mock_execute_agent
    )

    tasks = [
        {"agent": "agent_one", "kwargs": {}},
        {"agent": "agent_two", "kwargs": {}},
        {"agent": "agent_three", "kwargs": {}}
    ]

    start = time.time()
    result = run_parallel_swarm(tasks)
    elapsed = time.time() - start

    assert result["status"] == "success"
    assert result["successful_agents"] == 3
    assert result["failed_agents"] == 0
    assert len(result["merged_result"]) == 3
    assert elapsed < 0.28


def test_result_merging(monkeypatch):
    from app.workflows import parallel_swarm

    def mock_execute_agent(name, **kwargs):
        return {"output": name}

    monkeypatch.setattr(
        parallel_swarm.agent_runtime,
        "execute_agent",
        mock_execute_agent
    )

    tasks = [
        {"agent": "agent_one", "kwargs": {}},
        {"agent": "agent_two", "kwargs": {}}
    ]

    result = run_parallel_swarm(tasks)

    assert result["merged_result"] == [
        {"output": "agent_one"},
        {"output": "agent_two"}
    ]


def test_individual_agent_failure(monkeypatch):
    from app.workflows import parallel_swarm

    def mock_execute_agent(name, **kwargs):
        if name == "failing_agent":
            return {"status": "error", "message": "Simulated failure"}

        return {"output": name}

    monkeypatch.setattr(
        parallel_swarm.agent_runtime,
        "execute_agent",
        mock_execute_agent
    )

    tasks = [
        {"agent": "working_agent", "kwargs": {}},
        {"agent": "failing_agent", "kwargs": {}}
    ]

    result = run_parallel_swarm(tasks)

    assert result["status"] == "partial_success"
    assert result["successful_agents"] == 1
    assert result["failed_agents"] == 1
    assert result["merged_result"] == [{"output": "working_agent"}]


def test_all_agents_fail(monkeypatch):
    from app.workflows import parallel_swarm

    def mock_execute_agent(name, **kwargs):
        return {"status": "error", "message": "Agent failed"}

    monkeypatch.setattr(
        parallel_swarm.agent_runtime,
        "execute_agent",
        mock_execute_agent
    )

    tasks = [
        {"agent": "agent_one", "kwargs": {}},
        {"agent": "agent_two", "kwargs": {}}
    ]

    result = run_parallel_swarm(tasks)

    assert result["status"] == "error"
    assert result["successful_agents"] == 0
    assert result["failed_agents"] == 2


def test_invalid_input():
    result = run_parallel_swarm([])

    assert result["status"] == "error"


def test_invalid_task():
    result = run_parallel_swarm([
        {"agent": "", "kwargs": {}}
    ])

    assert result["status"] == "error"


@pytest.fixture
def collector_reads(monkeypatch):
    row = dict(student_id="STU003", marks=38, assignments=42, backlogs=2,
               attendance=45, internship_status="Not Started", placement_status="Not Ready")
    reads = {}
    for source in ("student", "academic", "attendance", "internship", "placement"):
        reads[source] = Mock(return_value=row.copy())
        monkeypatch.setattr(f"app.tools.{source}_tools.get_student", reads[source])
    monkeypatch.setattr("app.runtime.agent_runtime.log_action", lambda *args: None)
    return reads


@pytest.fixture
def waits(monkeypatch):
    delays = []
    monkeypatch.setattr("app.workflows.parallel_swarm.sleep", delays.append)
    return delays


def test_timeout_recovers_only_failed_collector(collector_reads, waits):
    placement = collector_reads["placement"]
    placement.side_effect = [NetworkTimeout("timed out"), placement.return_value]
    result = CoordinatorAgent().run("Collect STU003")

    assert result["status"] == "success"
    assert result["placement"]["placement_status"] == "Not Ready"
    assert waits == [0.25]
    assert placement.call_count == 2
    for source, read in collector_reads.items():
        if source != "placement":
            read.assert_called_once_with("STU003")
    assert all(call.args == ("STU003",) for call in placement.call_args_list)


def test_persistent_timeout_requires_review(collector_reads, waits):
    collector_reads["placement"].side_effect = NetworkTimeout("timed out")
    result = CoordinatorAgent().run("Collect STU003")

    assert result["status"] == "error" and result["review_required"]
    assert "placement_agent (attempts: 4)" in result["message"]
    assert collector_reads["placement"].call_count == 4
    assert waits == [0.25, 0.5, 1.0]


@pytest.mark.parametrize("evidence", [None, {"student_id": "STU003", "placement_status": "Ready"}])
def test_missing_or_conflicting_evidence_requires_review(collector_reads, waits, evidence):
    collector_reads["placement"].return_value = evidence
    result = CoordinatorAgent().run("Collect STU003")

    assert result["status"] == "error" and result["review_required"]
    assert "verify the placement record" in result["message"]
    assert waits == []


def test_configuration_error_requires_review_without_retry(collector_reads, waits):
    error = ConnectionError("MongoDB connection failed")
    error.__cause__ = ConfigurationError("Invalid configuration")
    collector_reads["student"].side_effect = error
    result = CoordinatorAgent().run("Collect STU003")

    assert result["status"] == "error" and result["review_required"]
    assert "contineo_agent (attempts: 1)" in result["message"]
    assert waits == []
