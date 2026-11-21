# Student Success implementation by lab

Select a lab to browse its source files. The entry point in the second column shows where to start reading. Shared modules appear in each lab that uses them.

Labs 01–13 contain focused excerpts. Run their demonstrations from the repository root so Python can load the shared modules and configuration. The [demonstration guide](../docs/demo.md) gives commands and expected results. Lab 14 contains the integrated application, its sample data, and its dependency list.

| Lab | Start with | What to trace |
| --- | --- | --- |
| [01 · Agent vs Chatbot](lab-01/) | [coordinator_agent.py](lab-01/app/agents/coordinator_agent.py) | Ask for a missing student ID, collect evidence, and revise an intervention after mentor feedback. |
| [02 · Tool-Using Agent](lab-02/) | [tool_registry.py](lab-02/app/runtime/tool_registry.py) | Follow a named tool from registration to its calculator, file, API, or student lookup implementation. |
| [03 · Skill Creation](lab-03/) | [skill_registry.py](lab-03/app/runtime/skill_registry.py) | Trace the research briefing and risk-analysis skills from registration through execution. |
| [04 · Memory and Retrieval](lab-04/) | [intervention_memory.py](lab-04/app/memory/intervention_memory.py) | Trace stored mentor decisions into the next recommendation and compare them with in-session assessment state. |
| [05 · MCP Connector](lab-05/) | [server.py](lab-05/app/mcp/server.py) | Follow client requests to the CSV resource, SQLite lookup, and Atlas-backed tools. |
| [06 · OpenClaw Runtime](lab-06/) | [SKILL.md](lab-06/skills/student-research/SKILL.md) | Follow a workspace skill into the Python runtime, registries, and audit log. |
| [07 · Agentic Node Graph](lab-07/) | [node_graph.py](lab-07/app/workflows/node_graph.py) | Follow collection, verification, risk assessment, retry, and checkpoint recovery. |
| [08 · Parallel Swarm](lab-08/) | [parallel_swarm.py](lab-08/app/workflows/parallel_swarm.py) | Trace the four concurrent student-data collectors and the coordinator's evidence checks. |
| [09 · Deep Research Agent](lab-09/) | [deep_research_agent.py](lab-09/app/agents/deep_research_agent.py) | Inspect the source catalog, compare claims, and follow the evidence links in the briefing. |
| [10 · Cloud Operations Agent](lab-10/) | [cloud_operations_agent.py](lab-10/app/agents/cloud_operations_agent.py) | Inspect incident diagnosis, the proposed rollback, and the simulator's recovery measurement. |
| [11 · Agentic SDLC Factory](lab-11/) | [release_lab.py](lab-11/app/workflows/release_lab.py) | Follow an attendance requirement through policy generation, boundary tests, staging, and release. |
| [12 · Safety and Governance](lab-12/) | [approval.py](lab-12/app/safety/approval.py) | Trace role checks, mentor approval, audit records, stale release detection, and rollback. |
| [13 · Discipline-Specific Agents](lab-13/) | [risk_agent.py](lab-13/app/agents/risk_agent.py) | Inspect the education worklet from synthetic training inputs to risk estimates and recommended support. |
| [14 · Capstone Project Studio](lab-14/) | [main.py](lab-14/app/main.py) | Follow a student case across the full application, from login and assessment to mentor review. |

## Run Lab 14

From the repository root, activate the project’s Python 3.12 environment and run these PowerShell commands. For login and live student workflows, configure the Atlas connection using the [environment example](lab-14/.env.example).

```powershell
cd lab-implementations/lab-14
python -m pip install -r requirements.txt
$env:PYTHONPATH = (Get-Location).Path
python -m streamlit run app/main.py
```
