# Student Success & Early Warning System — professor demonstration guide

**Opening line.** “We start with one student record. Four collectors assemble the evidence, a model estimates academic risk, and a recommendation agent proposes an intervention. A mentor reviews it, and the next assessment uses that decision.”

This guide follows the fourteen-lab curriculum. Labs 1–12 have executable demonstrations. Labs 13 and 14 describe how to present the project as a domain worklet and a capstone, subject to the professor’s assignment. The campus examples in the syllabus are adapted to student success.

## Before the demonstration

1. Use the project’s Python 3.12 environment. For a fresh environment, install the dependencies with `python -m pip install -r requirements.txt pytest`. Check that the project’s `.env` points to the intended demo database.
2. Prepare a synthetic student account linked to an at-risk profile and a mentor account. The graph demonstration uses `STU003`. Open separate browser sessions for the two roles so you can show the same intervention from both sides. Student View creates pending proposals when it assesses an at-risk student. Use a demo contact if you plan to approve one, since approval can send email.
3. Run these lines in PowerShell. Keep the UI terminal open. Use a second PowerShell window in the same environment and directory for the lab commands.

```powershell
cd "D:\Agentic AI\agentic-ai"
$env:PYTHONPATH = (Get-Location).Path
python -m streamlit run app/main.py
```

Open the local URL printed by Streamlit. **Student View** shows the assessment, recommended actions, and intervention history. **Intervention View** is the mentor’s review queue. **Mentor labs** contains Research briefing, Cloud incident, and Release review. Login and the live student workflow use Atlas. The research CLI and the fixture-based tests below can run locally.

## Lab 1 — Agent vs Chatbot

**Learning objective.** Show how the workflow asks for missing information, gathers evidence, and revises a proposed action after receiving feedback.

**How it works.** The coordinator asks for a student ID when the request omits one. With an ID, it gathers the student’s records. In Student View, a verified risk assessment can lead to a pending intervention. The recommendation agent reads the mentor’s decision on the next assessment and can revise the proposal.

**Live demo.**

1. Run `python -m app.agents.coordinator_agent`. Enter **Collect student information** and show the request for a student ID. Enter `STU003` and show the collected evidence.
2. Open Student View for a synthetic at-risk student with a pending attendance proposal. In the mentor session, reject that proposal with **Timetable clash** feedback.
3. Refresh Student View. For a first rejection with that feedback, show the revised asynchronous check-in proposal. Lab 4 follows the same case to show how the review persists across sessions.

**Point to make.** The student ID lets the coordinator gather evidence, and the mentor’s feedback changes the next proposed action. [Coordinator](../app/agents/coordinator_agent.py) · [Recommendation agent](../app/agents/recommendation_agent.py)

## Lab 2 — Tool-Using Agent

**Learning objective.** Show a computation and an external read through the same tool interface. A tool is a named callable with arguments and a result. The runtime looks up that name, invokes the function and records the execution outcome.

**Terminal demo.** Run the following in order. The first two commands use local code; the file tool launches the project’s MCP server, and the mock API uses the configured Atlas fixture.

```powershell
python -c "from app.runtime.agent_runtime import agent_runtime as r; print(r.list_tools())"
python -c "from app.runtime.agent_runtime import agent_runtime as r; print(r.execute_tool('calculate_percentage', part=10, total=100))"
python -c "from app.runtime.agent_runtime import agent_runtime as r; print(r.execute_tool('read_student_file').splitlines()[0])"
python -c "from app.runtime.agent_runtime import agent_runtime as r; print(r.execute_tool('mock_student_api', student_id='STU003').get('source'))"
```

**Expected evidence.** Show the tool names, the numeric answer `10.0`, the CSV header, and the response source `mock_api`. The cloud simulator uses this same percentage tool in Lab 10. Tool selection in these examples is explicit in the calling workflow. [Tool registry](../app/runtime/tool_registry.py)

## Lab 3 — Skill Creation

**Learning objective.** Package a multi-step capability so two callers can reuse it. The `research_summary` skill accepts a topic, selects or accepts sources, validates evidence, compares claims, and produces a structured briefing. Its inputs and outputs give callers a repeatable contract.

**Live demo.**

1. Run `python -m app.research.research_agent`. Point to the research question, evidence table, executive summary, and follow-up questions in the JSON output.
2. Sign in as a mentor. Open **Mentor labs → Research briefing**, enter **Student risk and attendance**, and click **Prepare briefing**.
3. Show the matching source identifiers in the UI and CLI. Both call the same registered skill. Lab 9 examines how the skill reaches its findings.

**Point to make.** “The terminal and dashboard each provide a different interface to one implementation.” [Skill registry](../app/runtime/skill_registry.py) · [CLI caller](../app/research/research_agent.py)

## Lab 4 — Memory & Retrieval

**Learning objective.** Demonstrate why a stored decision matters. A paused dashboard assessment lives in Streamlit session state. An intervention, its review status, and mentor feedback live in MongoDB and can influence a later session.

**Live demo.**

1. In Student View, choose a synthetic at-risk profile via its student login. Note a pending recommendation, such as an attendance intervention.
2. In the separate mentor session, open **Intervention View**, enter the same student ID, click **Load Interventions**, and select **Pending**. Enter **Timetable clash** on that proposal and click **Reject Intervention**.
3. Refresh the student page and inspect the decisions and plan. For a first rejection with that feedback, expect an asynchronous check-in proposal. Show the original decision in the mentor’s **Rejected** queue. Sign out and back in to demonstrate persistence.
4. If that fixture already has several prior reviews, use a fresh demo proposal or run `python -m pytest -q tests/test_lab_workflows.py::test_mentor_rejection_changes_proposal` for a reproducible example.

**Why the plan changes.** The recommendation agent retrieves this student’s history, matches the original proposal, and checks the feedback for scheduling terms. A previously approved plan produces a follow-up decision. This is explicit retrieval and decision logic. [Intervention memory](../app/memory/intervention_memory.py) · [Recommendation agent](../app/agents/recommendation_agent.py)

## Lab 5 — MCP-Style Connector

**Learning objective.** Access different sources through one Model Context Protocol server. The client starts the server as a subprocess, initializes a session over standard input/output, then reads a resource or calls a named tool. The server translates those requests into file or database operations.

**Terminal demo.** From the project root, initialize the local SQLite demo records from the synthetic CSV, then make three requests:

```powershell
python -m app.database.seed
python -c "from app.mcp.client import get_student_file; print(get_student_file().splitlines()[0])"
python -c "import asyncio; from app.mcp.client import call_mcp_tool; print(asyncio.run(call_mcp_tool('get_student_from_sqlite', {'student_id':'STU003'}))['student_id'])"
python -c "from app.mcp.client import get_student_api_data; r=get_student_api_data('STU003'); print(r.get('source'), r.get('student_id'))"
```

**Expected evidence.** A CSV header comes from the resource, `STU003` comes from SQLite, and `mock_api STU003` comes from the Atlas-backed mock API. The graph uses a separate single-student Atlas tool on this same server to verify academic evidence. The SQLite seed writes to the local lab database. [MCP client](../app/mcp/client.py) · [MCP server](../app/mcp/server.py)

## Lab 6 — OpenCLA/OpenClaw Runtime

**Learning objective.** Explain how a runtime discovers capabilities, executes them and leaves an audit trail. Inside the app, the Python runtime has agent, skill and tool registries as well as memory operations. At the OpenClaw boundary, a workspace skill describes when to run the project’s research CLI and how to interpret its sources.

**Terminal demo.**

```powershell
python -c "from app.runtime.agent_runtime import agent_runtime as r; print(r.list_agents()); print(r.list_skills())"
python -m app.research.research_agent
python -c "from app.runtime.audit_logger import get_audit_logs; x=get_audit_logs()[-1]; print(x['action'], x['result'])"
```

Expect `research_summary` in the registry and a recent `execute_skill:research_summary` success record when the demo is the only active caller. With the OpenClaw CLI installed and this repository configured as its workspace, run `openclaw skills info student-research --json`. Show the workspace source and eligibility fields. Discovery and direct skill execution are the verified integration points. A live model-driven OpenClaw run requires a separately configured model and gateway. [Workspace skill](../skills/student-research/SKILL.md) · [Python runtime](../app/runtime/agent_runtime.py)

## Lab 7 — Agentic Node Graph

**Learning objective.** Show dependencies, bounded retries and resuming from a checkpoint. Collection supplies the student snapshot. MCP verification checks key fields against that snapshot. Only then does risk analysis run. The model uses attendance, marks, assignments and backlogs.

**Live demo.**

1. Run `python -m app.workflows.node_graph --demo-recovery STU003`. Watch Nodes 1 and 2 finish. Node 3 deliberately fails, retries once immediately, then pauses.
2. **Copy the exact resume command printed by the program.** It contains the run ID associated with that checkpoint. Run it, even in a new terminal with the same environment and directory.
3. Point to **Reusing completed data collection and MCP verification**, followed by **[Node 3]** and the risk result. The successful resume removes the CLI checkpoint. This demo injects the fault only in the first command.
4. For ordinary execution, run `python -m app.workflows.node_graph`, enter `STU003`, and answer `n` after the initial assessment. For an offline recovery exhibit, run `python -m pytest -v -s tests/test_lab_workflows.py::test_resume_from_disk_skips_completed_nodes`.

**Point to make.** A retry re-enters the failed risk node within the run. A resume starts a later invocation from saved progress. Collection and MCP failures pause the dependent work; inconsistent evidence requires fresh collection. The UI’s **Resume assessment** uses the current session, while CLI checkpoints survive a process restart. [Graph and checkpoint routing](../app/workflows/node_graph.py)

## Lab 8 — Parallel Swarm

**Learning objective.** Show where parallel execution is appropriate and where a dependency requires waiting. The coordinator sends one student ID to four roles: Contineo retrieves the student record, LMS retrieves academic and attendance evidence, and the internship and placement collectors retrieve career status. These project adapters read repository data.

**How it works.** A thread pool runs independent collectors concurrently. The swarm returns per-agent outcomes, merged successes and errors. The coordinator checks for missing or conflicting evidence before handing the combined record to the graph. A successful sibling can finish even when another collector fails; the downstream assessment requires a complete set.

**Terminal demo.** Run `python -m app.agents.coordinator_agent` and enter **Collect student information for STU003**. Show the academic, attendance, internship and placement fields in the merged result. Then demonstrate the concurrency and failure checks on isolated fixtures:

```powershell
python -m pytest -v tests/test_parallel_swarm.py::test_parallel_execution tests/test_parallel_swarm.py::test_individual_agent_failure tests/test_lab_workflows.py::test_swarm_and_audit_report_domain_failure
```

To demonstrate recovery offline, run:

```powershell
python -m pytest -v tests/test_parallel_swarm.py::test_timeout_recovers_only_failed_collector tests/test_parallel_swarm.py::test_persistent_timeout_requires_review
```

In the first test the placement lookup times out once. Its second attempt uses the same student ID, and the coordinator validates its result alongside the three successful collectors' evidence. In the second test placement keeps timing out. The test checks the configured retry delays (0.25, 0.5 and 1 second) and confirms that the coordinator flags the case for review after the fourth attempt.

**Point to make.** The merged record demonstrates integration. The timed concurrency test and mixed-outcome test establish the behavior that a finished record alone cannot show. [Coordinator](../app/agents/coordinator_agent.py) · [Swarm runner](../app/workflows/parallel_swarm.py)

## Lab 9 — Deep Research Agent

**Learning objective.** Trace an answer back to evidence and identify what the evidence can establish. A question selects matching entries from a local project catalog. The agent requires three sources with unique IDs and fields for claim, evidence, limitation and relevance. It compares normalized claims, detects simple explicit negations, and turns listed limitations into gaps and follow-up questions.

**Live demo.**

1. In **Mentor labs → Research briefing**, ask **Which indicators contribute to student risk?** and click **Prepare briefing**.
2. Point to the agreement about low attendance. The risk explanation and synthetic-label generator both mention it. Open one of the cited files and show the relevant attendance condition.
3. Read the limitation **Labels are synthetic**. Ask the professor what additional evidence would support use with real students. A suitable answer is an evaluation against observed outcomes from a separate student cohort.
4. Try **Ocean tides**. The current catalog has too few matching sources, so the UI shows a validation message. This illustrates the boundary of local retrieval.

**Point to make.** The briefing is grounded in curated project evidence. Its comparisons use wording rules, and its follow-up questions are generated from recorded limitations. [Research agent](../app/agents/deep_research_agent.py) · [Evidence catalog](../app/agents/research_sources.json)

## Lab 10 — Cloud Operations Agent

**Learning objective.** Demonstrate an operational decision with a measurable recovery signal. The calculator tool measures errors in 100 simulated portal responses. The cloud agent compares the observed error rate with the baseline. At 1.5 times baseline it reports degraded service; at twice baseline it reports critical service. A raised rate plus an error log and matching service deployment can trigger a rollback request. Insufficient evidence leads to further investigation.

**Live demo.**

1. Open **Mentor labs → Cloud incident**. If an earlier demo already restored v1, click **Restart deployment exercise**.
2. Show **10%** and **Running v2 · critical · rollback**. Ten failed requests against a 1% baseline give a tenfold increase. The recent release is a suspected cause.
3. Pause at the approval request. Click **Approve simulated rollback**. The mentor action is audited, the simulator switches to v1, and the app measures again.
4. Show **1%** and **Running v1 · normal · monitor**. The second measurement demonstrates recovery. The version change is local to this Streamlit session.

**Point to make.** Lab 7 recovers a task by resuming computation. Lab 10 recovers a simulated service by changing its version and observing the new error rate. [Cloud operations agent](../app/agents/cloud_operations_agent.py) · [Simulator](../app/ui/labs.py)

## Lab 11 — Agentic SDLC Factory

**Learning objective.** Follow one requirement through generation, testing, human release approval and monitoring. The factory supports a specific requirement form, **Flag attendance below N%**, with N between 1 and 100. It turns that threshold into a Python function and checks its boundary behavior before staging a versioned revision in SQLite.

**Live demo.**

1. Open **Mentor labs → Release review**. Note the current active cutoff. A fresh simulator defaults to 60%. Set the sample attendance slider to **62**.
2. Enter **Flag attendance below 65%** and click **Build and test policy**. Identify the new revision marked **tested**.
3. Expand **Acceptance checks for revision …**. Show the generated function and its three cases: 64 is flagged, 65 is clear, and 100 is clear. Use **Download policy module** if the professor asks to see the deliverable.
4. Click **Approve** on that revision. At 62% attendance the sample is now flagged. If a previous demo already had 65% active, show the boundary directly by moving the slider between 64 and 65.

**Point to make.** Building and testing a policy produces a candidate. Approval changes the active simulator version. The student dashboard continues to use its own trained risk model. [Release factory](../app/workflows/release_lab.py)

## Lab 12 — Safety & Governance

**Learning objective.** Demonstrate who may change a policy, what is recorded, and how a bad change can be reversed. The mentor page enforces the role; the release transition also checks the role and actor. Each staged revision remembers the active version on which it was based. Approval and rollback update release state and write an audit event in one SQLite transaction.

**Live demo.**

1. In the student session, show the available student navigation. Switch to the mentor session and open **Release review**.
2. With the same active version, stage **Flag attendance below 66%** and **Flag attendance below 70%**. Note their revision IDs before clicking any approval.
3. Approve the 66% revision. Then try to approve the 70% revision. Expect a warning that the release state changed. Its review was based on an earlier active revision. To consider 70% again, stage a fresh revision.
4. Click **Rollback** on the active 66% revision. Confirm the previous cutoff returns. Expand **Review history** and point to the actor, revision ID, action, and time.
5. To show the role guard and stale-approval checks without changing classroom demo state, run `python -m pytest -v tests/test_lab_workflows.py::test_release_lifecycle`. For student-intervention governance, `python -m pytest -v tests/test_approval.py` also demonstrates parent opt-out, approval before notification, and duplicate-send handling with mocks.

**Point to make.** An approval applies to a specific revision and starting state. The audit trail lets a reviewer reconstruct the decision after a rollback. [Release transitions](../app/workflows/release_lab.py) · [Intervention approvals](../app/safety/approval.py)

## Lab 13 — Discipline-specific agents (worklet presentation)

The curriculum assigns a discipline-specific worklet. This repository supplies an **education-domain** example. Confirm with the professor whether that fulfills the assigned worklet; a mechanical, civil or electrical worklet would require its own domain inputs, tools and evaluation.

**Suggested demonstration using the existing project.** Open Student View for the demo profile. Point to the risk probability, then trace one displayed reason back to the student’s attendance, marks, assignments or backlogs. Show the corresponding proposed support action. Explain that internship and placement status inform recommendations, while the model uses four academic inputs. The model is trained on synthetic labeled data. The displayed probability is a model estimate whose real-world usefulness would need separate evaluation. [Risk model](../app/ml/risk_model.py) · [Recommendation logic](../app/agents/recommendation_agent.py)

## Lab 14 — Capstone Project Studio (integrated presentation)

**Capstone question.** Can the team show one complete student case from evidence collection through human review and an observable change in the next plan? The existing workflows support that presentation. Formal capstone completion and team assessment depend on the course rubric.

**Suggested team demo.**

1. **Student presenter:** Open the synthetic profile. Show the composite risk probability and one reason.
2. **Workflow presenter:** Explain where the four collectors join, then show the Lab 7 resume output. Identify which completed steps were reused.
3. **Mentor presenter:** Reject a pending recommendation with **Timetable clash**. Refresh the student view and show the revised action plus the historical review record.
4. **Evaluation presenter:** Show one fixture-based test for the feedback loop and one for rollback. End with the four worklet outputs on screen or in the intervention history: **risk score, reasoned flag, action plan, intervention log**.

## If you have five minutes

Spend two minutes on **student risk → mentor feedback → revised plan** (Labs 1, 4, 8 and the capstone). Spend one minute showing the **paused and resumed graph** (Lab 7). Use the remaining two minutes for **cloud rollback** and **release boundary tests** (Labs 10–12). Keep the research CLI and the MCP commands ready if the professor asks how tools, skills and evidence retrieval differ.
