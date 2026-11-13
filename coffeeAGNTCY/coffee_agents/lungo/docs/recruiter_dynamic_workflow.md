 
``` 
 ---
 Architecture Overview

 User Request
     |
     v
 [main.py] FastAPI server (port 8882)
     |
     v
 [agent.py] Root Supervisor Agent (ADK LlmAgent)
     |--- tool: recruit_agents()  --> [recruiter_client.py] --> Remote Recruiter Service (A2A, port 8881)
     |                                                          Stores results in session state
     |
     |--- sub-agent: DynamicWorkflowAgent (BaseAgent)
               |
               v
          [dynamic_workflow_agent.py]
               Reads recruited agents from session state
               Creates RemoteA2aAgent instances at runtime
               Wraps them in ParallelAgent for concurrent execution
```

## Numbers in data parts (protobuf `Struct`)

The recruiter service runs on a2a-sdk 1.x and answers A2A v1.0 only on its JSON-RPC endpoint. The supervisor card declares `protocol_version="1.0"`, so the supervisor speaks A2A v1.0 to it. A data part travels as a protobuf `Struct`, and a `Struct` stores every number as a double. This does not depend on the A2A version: v1.0 and v0.3 both write `10201.0` into the JSON-RPC body.

- **Inbound** (`recruiter_client._restore_known_ints`): `"id": 10201` reads back as `10201.0`, so only the key `id` is converted back to an `int`. Other whole-valued floats, such as a `score` of `1.0`, stay floats because the recruiter model declares `score` as a float.
- **Outbound** (`evaluate_agent`): the OASF record is sent as a data part, and a2a-sdk writes `10201.0` into the JSON-RPC body. This is a known limitation and is not worked around: the recruiter service reads only typed data parts, so a JSON text part would be ignored, and converting every whole float to an int would corrupt genuine floats. The effect is cosmetic, because the records end up as JSON text in LLM prompts.
- **Recruiter server side** (`agent_recruiter/common/a2a_helpers.py`, `_plain`): the server turns every whole-valued float it receives back into an `int`, because the data it reads (OASF records, `evaluation_criteria`, metadata) has no genuine float fields. The id-only rule above applies on the supervisor side only, where `score` lives. A genuine whole-valued float in an inbound record, such as `1.0`, is not preserved.
- A complete fix needs a schema-aware conversion in a2a-sdk. The behavior against the live recruiter image is not yet covered by a contract test.
