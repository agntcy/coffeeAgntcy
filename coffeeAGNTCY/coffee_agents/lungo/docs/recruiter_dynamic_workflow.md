 
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

## Numbers in data parts (A2A v0.3 bridge)

The recruiter service still speaks A2A v0.3, so the supervisor reaches it through a2a-sdk's v0.3 compatibility transport. A data part travels as a protobuf `Struct`, and a `Struct` stores every number as a double.

- **Inbound** (`recruiter_client._restore_known_ints`): `"id": 10201` reads back as `10201.0`, so only the key `id` is converted back to an `int`. Other whole-valued floats, such as a `score` of `1.0`, stay floats because the recruiter model declares `score` as a float.
- **Outbound** (`evaluate_agent`): the OASF record is sent as a data part, and the compat layer (`a2a/compat/v0_3/conversions.py`, `to_compat_part`) writes `10201.0` into the JSON-RPC body. This is a known limitation and is not worked around: the recruiter service reads only typed data parts, so a JSON text part would be ignored, and converting every whole float to an int would corrupt genuine floats. The effect is cosmetic, because the records end up as JSON text in LLM prompts.
- A complete fix needs a schema-aware conversion in a2a-sdk's compat layer. The behavior against the live recruiter image is not yet covered by a contract test.
