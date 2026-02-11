 
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