# Tasks

## 1. Agent chart values and ConfigMaps

- [x] 1.1 Add `workflowApiUrl: ""` and `workflowApiKey: ""` under `config:` in `values.yaml` of `auction-supervisor`, `colombia-farm`, `logistics-supervisor`, `recruiter-supervisor`; verify with a grep that each of the four files has both keys and no other chart does
- [x] 1.2 Add conditional `WORKFLOW_API_URL` / `WORKFLOW_API_KEY` entries to those four `templates/configmap.tpl.yaml`; verify `helm template <chart> --set config.workflowApiUrl=u --set config.workflowApiKey=k` shows both, and a default `helm template` shows neither, for each of the four
- [x] 1.3 Minor-bump the four charts' `version` (`colombia-farm` 0.1.3 -> 0.2.0, the others 0.1.2 -> 0.2.0); verify `task helm:check-versions` passes for them

## 2. Local cluster

- [x] 2.1 Add a `$workflowApi` config dict (URL `http://agentic-workflows-api:9105`, key from `env "WORKFLOW_API_KEY"` defaulting to `TheAnswerIs42`) to `config-overrides.yaml.gotmpl` and merge it only into the four agents; verify the rendered overrides contain both values for those four and for no brazil-farm, vietnam-farm, logistics-farm, logistics-accountant, logistics-shipper, logistics-helpdesk or recruiter
- [x] 2.2 Update `local-cluster/Chart.yaml` dependency pins for the four bumped charts and minor-bump its own `version` (0.5.0 -> 0.6.0); verify `helm dependency list` and `task helm:check-versions` report no mismatch

## 3. Docs and final checks

- [x] 3.1 Document `config.workflowApiUrl` / `config.workflowApiKey` where chart config is described (grep README, `docs/`, `local-cluster/README.md`), and add a `CHANGELOG.md` Unreleased entry; verify `task dashes:check` and the markdown link check pass
- [x] 3.2 Run `helm lint --strict` and `helm template` on the four charts plus `local-cluster`, and confirm the other agent charts render identically to before; verify no errors and no diff for the unchanged charts
