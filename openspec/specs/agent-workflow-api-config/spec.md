# agent-workflow-api-config Specification

## Purpose
Defines how Lungo agent Helm charts let an operator point an agent at the
Agentic Workflows API, so workflow events and catalog lookups work in Helm
deployments the same way they do in Docker Compose.

## Requirements

### Requirement: Workflow-calling agent charts expose the workflow API settings as values
The charts of agents that may call the Agentic Workflows API (`auction-supervisor`,
`logistics-supervisor`, `recruiter-supervisor`, `colombia-farm`) SHALL accept `config.workflowApiUrl`
and `config.workflowApiKey` in its `values.yaml`, defaulting to empty.

#### Scenario: Values are declared
- **WHEN** one of those charts' default `values.yaml` is read
- **THEN** `config.workflowApiUrl` and `config.workflowApiKey` are present with empty-string defaults

### Requirement: Values are rendered into the agent ConfigMap
Each agent chart SHALL render a non-empty `config.workflowApiUrl` as
`WORKFLOW_API_URL` and a non-empty `config.workflowApiKey` as
`WORKFLOW_API_KEY` in its ConfigMap, which the agent container loads as
environment variables.

#### Scenario: Both values set
- **WHEN** a chart is rendered with `config.workflowApiUrl=http://agentic-workflows-api:9105` and `config.workflowApiKey=k`
- **THEN** the ConfigMap contains `WORKFLOW_API_URL: "http://agentic-workflows-api:9105"` and `WORKFLOW_API_KEY: "k"`

#### Scenario: Only the URL set
- **WHEN** a chart is rendered with only `config.workflowApiUrl` set
- **THEN** the ConfigMap contains `WORKFLOW_API_URL` and does not contain `WORKFLOW_API_KEY`

### Requirement: Unset values do not override application defaults
A chart SHALL NOT emit `WORKFLOW_API_URL` or `WORKFLOW_API_KEY` when the
corresponding value is empty, so the agent's built-in default applies.

#### Scenario: Default render
- **WHEN** a chart is rendered with default values
- **THEN** the ConfigMap contains neither `WORKFLOW_API_URL` nor `WORKFLOW_API_KEY`

### Requirement: Charts of agents that never call the API are unchanged
Charts of agents that do not call the Agentic Workflows API SHALL NOT gain the
`workflowApiUrl` / `workflowApiKey` values or the corresponding ConfigMap keys.

#### Scenario: Non-calling agent chart
- **WHEN** `brazil-farm`, `vietnam-farm`, `logistics-farm`, `logistics-accountant`, `logistics-shipper`, `logistics-helpdesk` or `recruiter` is rendered
- **THEN** its ConfigMap contains neither `WORKFLOW_API_URL` nor `WORKFLOW_API_KEY`

### Requirement: Local cluster configures the workflow API for calling agents
The `local-cluster` overrides SHALL set `config.workflowApiUrl` to the
in-cluster `agentic-workflows-api` service and `config.workflowApiKey` to the
key that service uses, for each workflow-calling agent chart in the umbrella.

#### Scenario: Local cluster render
- **WHEN** `local-cluster` is rendered with its overrides
- **THEN** each of the four workflow-calling agent ConfigMaps contains `WORKFLOW_API_URL` pointing at `http://agentic-workflows-api:9105` and a `WORKFLOW_API_KEY` equal to the API's configured key

### Requirement: Chart versions are bumped as minor
Each chart whose content changes SHALL have its `version` minor-bumped (new
configuration surface), and the
`local-cluster` dependency pins SHALL match the bumped versions.

#### Scenario: Version guard passes
- **WHEN** `task helm:check-versions` runs after the change
- **THEN** it reports no chart changed without a version bump
