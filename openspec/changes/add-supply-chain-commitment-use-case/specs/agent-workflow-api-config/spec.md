# Spec Delta

## MODIFIED Requirements

### Requirement: Workflow-calling agent charts expose the workflow API settings as values
The charts of agents that may call the Agentic Workflows API (`auction-supervisor`,
`logistics-supervisor`, `recruiter-supervisor`, `colombia-farm`, `supply-chain-buyer`) SHALL accept `config.workflowApiUrl`
and `config.workflowApiKey` in its `values.yaml`, defaulting to empty.

#### Scenario: Values are declared
- **WHEN** one of those charts' default `values.yaml` is read
- **THEN** `config.workflowApiUrl` and `config.workflowApiKey` are present with empty-string defaults

### Requirement: Charts of agents that never call the API are unchanged
Charts of agents that do not call the Agentic Workflows API SHALL NOT gain the
`workflowApiUrl` / `workflowApiKey` values or the corresponding ConfigMap keys.

#### Scenario: Non-calling agent chart
- **WHEN** `brazil-farm`, `vietnam-farm`, `logistics-farm`, `logistics-accountant`, `logistics-shipper`, `logistics-helpdesk`, `recruiter`, `supply-chain-supplier` or `supply-chain-logistics` is rendered
- **THEN** its ConfigMap contains neither `WORKFLOW_API_URL` nor `WORKFLOW_API_KEY`

### Requirement: Local cluster configures the workflow API for calling agents
The `local-cluster` overrides SHALL set `config.workflowApiUrl` to the
in-cluster `agentic-workflows-api` service and `config.workflowApiKey` to the
key that service uses, for each workflow-calling agent chart in the umbrella.

#### Scenario: Local cluster render
- **WHEN** `local-cluster` is rendered with its overrides
- **THEN** each of the five workflow-calling agent ConfigMaps contains `WORKFLOW_API_URL` pointing at `http://agentic-workflows-api:9105` and a `WORKFLOW_API_KEY` equal to the API's configured key
