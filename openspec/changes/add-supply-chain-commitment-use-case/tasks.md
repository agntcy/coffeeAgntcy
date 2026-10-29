# Tasks

Paths are relative to `coffeeAGNTCY/coffee_agents/lungo/` unless they start
with `/` (repo root).

## 1. Spike and vendoring

- [x] 1.1 Spike the App SDK group chat against the installed SDK (0.6.0)
      source: who can publish, whether members can stay silent, and how
      broadcast replies are routed. Record the outcome and the transport
      decision in `design.md` under D3. Verify: D3 names the chosen API
      and the reasons, and task 7.2 checks one reply per addressee live.
- [x] 1.2 Copy the four skills from upstream commit `948730e` into
      `third_party/l9_skills/`, unmodified, and write `PROVENANCE.md` (URL,
      commit, versions, date, the no-licence and do-not-push note, a
      sha256 manifest). Add `tests/unit/supply_chain/test_l9_vendor_integrity.py`.
      Verify: the test passes and `diff -r` against the upstream clone shows
      no differences.
- [x] 1.3 Add `--exclude-dir third_party` to `/scripts/checks/check_dashes.bash`
      and `/scripts/checks/fix_dashes.bash`. Make `find_strings.bash` honor
      `--exclude-dir` and `--exclude-glob` in git mode too (as exclude
      pathspecs). Extend the bats tests with exclusion cases, and add the
      lungo `runs/` path to the root `/.gitignore`. Verify: the affected
      bats files and `check_dashes.bash` pass under bash 5 with the
      vendored files present, and shellcheck and shfmt are clean.

## 2. Shared core: fixtures, envelope, record, checker

- [x] 2.1 Write `agents/supply_chain/fixtures/scenario_v1.json` with the four
      cases and per-party slices, plus the slice loader (`common/fixtures.py`).
      Verify: unit tests assert the use-case numbers (400/350/250 tonnes,
      ready times, a $15,000 standard total, a $19,000 total with C
      expedited, a 2-day expedite) and that each slice holds only its own
      party's fields.
- [x] 2.2 Implement the envelope (`common/envelope.py`): the
      encode/decode, the addressing gate and the noop. Verify: unit tests
      cover addressing, self-messages, non-JSON input, apostrophes and
      quotes in `body`, and that the end token cannot appear from `body`.
- [x] 2.3 Implement the commitment record model and its JSON Schema export
      (`common/record.py`). Verify: unit tests for valid, missing-field and
      version-mismatch confirmation cases.
- [x] 2.4 Implement the deterministic checker (`common/checker.py`). Verify:
      a unit test per spec scenario (feasible PASS, all-standard
      LATE_LOT+FALSE_COMMITMENT, infeasible commit with INVENTED_CAPACITY,
      infeasible withhold PASS, FALSE_WITHHOLD, STALE_PLAN,
      MISSING_CONFIRMATION, MILESTONE_UNRESOLVED, OVER_BUDGET,
      QUANTITY_MISMATCH), and that claimed arrival or cost values in the
      record are ignored in favor of recomputed ones.
- [x] 2.5 Write the role base prompts (`common/prompts.py`) for the Buyer,
      the suppliers and Logistics. Verify: a unit test renders each role
      for each case and asserts that no other party's figures appear (spec:
      five agents with separate information).

## 3. Group member agents

- [x] 3.1 Implement the supplier agent (`agents/supply_chain/supplier/`:
      card, agent, executor, server; `SUPPLIER_ID` selects the slice and the
      card name). It includes the negotiation, confirm, ACCORD-receiver and
      CONCORD-receiver handlers, and the `concord_forge` tool, which runs a
      subprocess without a shell. Verify: unit tests with a fake LLM cover
      the noop gate, the single-Message reply, the forge tool invocation,
      and ACCORD memory independence (no peer replies in the prompt).
- [x] 3.2 Implement the Logistics agent (`agents/supply_chain/logistics/`)
      on the same pattern. Verify: the same unit tests pass for Logistics,
      and the case overrides change capacity in `infeasible`.
- [x] 3.3 Add OASF records for the four member agents (the Buyer's comes
      with its card in 4.1) and the placeholder-secret policy in each
      server. Verify: `test_agent_cards.py` and the
      placeholder-secret tests are extended and pass, and each OASF `name`
      equals its `AgentCard.name`.

## 4. Buyer supervisor and strategies

- [x] 4.1 Scaffold `agents/supervisors/supply_chain/` (`main.py` routes per
      D9, card, shared factory, suggested prompts, case and configuration
      extraction, a `_WORKFLOW_NAME` matching the catalog). Verify: unit
      tests for prompt extraction and explicit-field precedence, the
      `l9_full` "not implemented" response, and the workflow-name drift
      test.
- [x] 4.1c Rework the suggested prompts (added 2026-10-27, see decisions
      N23 and `docs/supply_chain_suggested_prompts.md`). In
      `selection.py` add the closing-tag rule (`(<case>/<run type>)`,
      case insensitive, `baseline`, `L9 hybrid`, `L9 full` and the
      identifiers) between the explicit fields and the model reading (D9).
      Rewrite `suggested_prompts.json` as 12 prompts grouped by goal
      (`DR-1`, `CE-1`, `IE-1`, `CC-4`), in the wording of the doc, each
      with its `case` and `configuration`. Make `GET /suggested-prompts`
      return only the `baseline` prompts when the runner's `l9_enabled` is
      false (D12). No frontend change. Verify: unit tests cover the tag
      rule (all run type spellings, an unknown tag falling through, explicit
      fields winning, the model not called when the tag gives both
      fields), that every prompt's tag equals its `case` and
      `configuration`, 12 prompts with L9 on, 4 and none mentioning L9 with
      L9 off, and that the existing `test_buyer_api.py` assertions are
      updated.
- [x] 4.2 Implement the moderator run loop: per-step `broadcast_message`
      group sessions (D3), `seq`
      assignment, the transcript, the run directory files, the timeouts and
      the limits. Verify: unit tests with a fake group transport cover the
      transcript ordering, the files written on success, failure and
      timeout, and the round-limit outcome.
- [x] 4.2b Live SLIM check (added 2026-10-27, see decisions N17 risk B).
      Start the SLIM server with Docker, run the supplier and logistics
      agents with a fake model, and send one `broadcast_message` step
      addressed to Supplier B only, then one addressed to three agents.
      Verify: exactly one reply per addressee, none from anyone else, the
      replies carry the right `reply_to`, and the Buyer persona can be
      called in-process in the same step. If this fails, stop and report
      before building 4.3 onward.
- [x] 4.2c Add the `INVALID` verdict and the `silent` flag (D8, added
      2026-10-27). `check` returns `INVALID` first when the record's reason
      is `timeout` or `protocol_error`; the run computes `silent` from the
      verdict, the record and the run signals (committed, five `confirm`
      for the recorded version, no rejected reply, no escalation, `FAIL`).
      Update the record builder's signals, the verdict model and the JSON
      Schema. Verify: unit tests for each new spec scenario (clean process
      with a late plan is `FAIL` and silent; an earlier rejection makes it
      not silent; `PASS` and `INVALID` are never silent; timeout and
      `protocol_error` on a feasible case are `INVALID`, `round_limit` is
      `FALSE_WITHHOLD`), and the existing checker tests still pass.
- [x] 4.2d Add the deployment switch `SUPPLY_CHAIN_L9_ENABLED` (D12, added
      2026-10-27). The Buyer rejects `l9_hybrid` with HTTP 400 when off
      (also in the runner, so no agent is contacted); members reply with an
      error to `accord_request` and `concord_request` without reading the
      skills directory, and never create the forge tool; `meta.json`
      records `l9_available`. Verify: unit tests for the spec scenarios in
      "A baseline run contains no ACCORD or CONCORD" (a baseline run with a
      fake LLM: no L9 text in any prompt, forge tool never bound, no
      protocol kinds; switch off: the skills directory is never read).
- [x] 4.3 Implement the `baseline` strategy plus the confirm round and the
      record builder (D4, D6). Verify: a fake-LLM test drives a commit, a
      withhold and a party rejection, and checks that the record status and
      confirmations follow D6. The test also asserts, for the real
      baseline strategy, what `test_l9_switch.py` asserts for a scripted
      one: no skill text in any prompt, no forge tool bound, no `accord_*`
      or `concord_*` message.
- [x] 4.3b Live baseline probe (added 2026-10-27, user decision "probe
      first"). Run case `ambiguous` with `baseline` against the real model
      at least five times through the runner (no UI), keep every run
      directory, and record in the decisions file how many runs were silent
      failures, other failures, passes and invalid, and what the Buyer,
      Logistics and the confirm round said about "delivery". Verify: the
      counts and the run directories exist. Stop and report to the user
      before building 4.4 onward. If silent failures are rare, task 4.3c
      applies (the failure is the aim; accepting the rate is not the path).
      Result of the first probe: 0 of 5 (see decisions N22), so 4.3c is
      open.
- [ ] 4.3c Refine the failing scenario (added 2026-10-27, user decision "we
      refine the examples until they fail silently"). Starting with
      `ambiguous` and `baseline`, change one thing at a time, re-run the
      probe (at least five runs per version), and stop when the baseline
      fails silently reliably. The allowed levers are agreed with the user
      before the first change (see decisions N24); each change is logged
      with what changed, why and the counts before and after. Give the
      scenario a version number in `meta.json`. Do not use any L9 run to
      choose a refinement, and freeze the version before task 4.5 runs.
      Every run's `meta.json` records `prompt_version`. Verify: the
      decisions file has the refinement log, the final version has the
      silent-failure counts, and the existing unit tests (checker,
      fixtures, prompts) still pass or are updated with the change.
      Progress (decisions N25): the original text was compared with ours
      and is applied faithfully; refinement 1 (option B, prompt version 2)
      gave 0 of 5 silent failures; refinement 2 (lever C, prompt version 3)
      gave 5 `FAIL`, all only `MILESTONE_UNRESOLVED` with correct plans, so
      it is an artefact of the checker rule and not counted. Refinement 3
      (user option 1: an unspecified milestone is not graded) gave 0 of 5
      silent failures, 5 passes. The baseline is still saved by Logistics
      flagging the late lot and by the arrival dates in the confirm request.
      Refinement 4 (lever D, no arrival dates in the confirm request,
      prompt version 4) and refinement 5 (Logistics gets its own meaning of
      "delivery", prompt version 5) each gave 0 of 5. Logistics already
      lists each lot's arrival and offers expedited for C in round 1, so the
      rescue is in the scenario data. The levers inside the original are
      used up. Refinement 6 (user: "option A first then B"; scenario
      transit 72 h -> 60 h so C is 4 hours late on the deadline day, the
      Buyer keeps the 17:00 deadline, prompt version 6) gave **5 of 5
      silent failures** for `ambiguous`/`baseline` (`LATE_LOT`,
      `FALSE_COMMITMENT`, 0 rejected replies). Option B was not needed.
      Still open: probe `explicit`, `infeasible` and `disruption` on
      baseline, then freeze the version (decisions N25).
      Progress (decisions N26, prompt version 7): `infeasible` 5 of 5 silent
      (after an option-naming artefact was fixed in the plan schema) and
      `ambiguous` 5 of 5 silent. `explicit` 0 of 5 (5 passes) and
      `disruption` 0 of 5 (5 correct withholds). A subtler delay for
      `disruption` (lever D1) was tried and reverted, also 0 of 5. The
      remaining levers change what the case is; awaiting the user's choice.
      Progress (decisions N27, user: "try B, then A"): lever B (Logistics
      answers only what it is asked, prompt version 8) made `ambiguous` and
      `infeasible` pass and was reverted. The hold-time lever (the deadline's
      time of day is in the Buyer's brief only, prompt version 9) gave
      `explicit` 10 of 10 silent, `infeasible` 5 of 5, `disruption` 2 of 5
      (about 1 in 10 a clean stale-approval failure), but `ambiguous` fell to
      2 of 15 with unchanged inputs (it was 10 of 10 at versions 6 and 7).
      Not frozen: baseline results vary between batches, so larger samples,
      repeated on another day, are needed first.
- [ ] 4.4 Implement the L9 bridge (`common/l9_bridge.py`) over the vendored
      initiator scripts. Verify: unit tests run the real scripts against
      canned receiver replies through a full ACCORD lock and a CONCORD
      SUCCESS and BEST_EFFORT, and show that script errors produce
      `protocol_error`.
- [ ] 4.5 Implement the `l9_hybrid` strategy (D5): the Buyer-LLM initiator
      choices, ACCORD, execution, CONCORD, and the decision step. Verify:
      a fake-LLM test asserts the phase order in the transcript, that the
      key terms come from the LLM's output, and that relayed messages equal
      the script stdout byte for byte.
- [ ] 4.6 Implement the disruption flow (D7) for both strategies. Verify:
      a fake-LLM       test shows the version 2 plan, version 1 confirmations not
      counted, and no injection when the first outcome is not committed.
      Baseline part done (decisions N26): `Moderator.inject_disruption`,
      private notice to Supplier C, group notice from the moderator, a fresh
      round budget, tests in `test_baseline.py`. The `l9_hybrid` resume
      (new CONCORD run under the locked contract) stays open with 4.5.
- [x] 4.7 Stream `message`, `record`, `verdict` and `status` events as JSON
      NDJSON, and run the checker after `RUN_END`. The verdict event
      carries `PASS`, `FAIL` or `INVALID` and the `silent` flag. Verify: a
      test parses every streamed line with `json.loads`, including text with
      apostrophes, asserts no agent-addressed message follows the verdict,
      and asserts that the `silent` flag is in the verdict event.
- [ ] 4.8 Add `strategies/l9_full.py` as a registered stub with a docstring
      naming the follow-up work (the initiator tools for the Buyer and the
      delegation tools), and document the extension point in
      `docs/supply_chain_commitment.md`. Verify: the test from 4.1 covers
      the stub.

## 5. Catalog, API contract and workflow docs

- [x] 5.1 Add the "Supply Chain Commitment" entry to
      `api/agentic_workflows/starting_workflows.json` (the topology from
      the spec), add `Secure Group Collaboration` to `patterns.py`, and add
      `supply_chain` to `catalog_types.py` and `transport_ui_enrichment.py`
      (SLIM). Verify: the `test_workflow_capabilities`,
      `test_workflow_endpoints` and `test_transport_ui_enrichment` tests
      are extended and pass.
- [x] 5.2 Add `supply_chain` to `schema/openapi/components/schemas.yaml`,
      regenerate the frontend OpenAPI types, and update
      `docs/workflow-instance_api.md` (skill
      `agentic-workflows-api-documentation-lungo`). Verify: the
      `tests/unit/openapi/*` tests pass.
- [x] 5.3 Write `api/agentic_workflows/docs/workflows/supply_chain_commitment.md`.
      Verify: the documentation endpoint returns it in the existing
      workflow-docs test pattern.

## 6. Frontend

- [x] 6.1 Add `supply_chain` to `patternUtils.ts`, `agenticWorkflowsApi.ts`,
      `urls.ts`, `vite-env.d.ts`, `.env.example` and the sidebar SLIM set.
      Verify: the vitest suites for `patternUtils`, `workflowCapabilities`,
      `workflowChatRouting` and `agenticWorkflowsApi` are extended and
      pass.
- [x] 6.2 Generalize the group streaming store (a discriminated union,
      JSON-first parsing) and keep the logistics behavior. Verify: the
      store tests cover both shapes, apostrophes, and that the existing
      logistics tests still pass.
- [x] 6.3 Render negotiation messages, the record card and the verdict card
      in `GroupCommunicationFeed`, and generalize the sender-to-node
      mapping. The verdict card shows `PASS`, `FAIL` or `INVALID`, and a
      "silent failure" badge with the line "all five parties confirmed"
      when the flag is true. Verify: component tests for each event type
      and for the badge, and the
      `chatStreamGraphHighlight` test is extended for Supplier B.
- [x] 6.4 Remove the hardcoded group slug in `agenticTopologyIdentityUiMap.ts`,
      and extend `resolveAgentSlug.ts` and `topologyNodeIcons.tsx` for the
      new labels. Verify: their tests are extended and pass, `npm run
      lint`, `npm run build` and `npm test` pass, and
      `frontend/docs/env-configuration.md` and
      `http-and-error-handling.md` are updated.

## 7. Local run: Compose and Makefile

- [x] 7.1 Add the `supply_chain` profile services to `docker-compose.yaml`
      (buyer, three supplier instances, logistics; the vendored skills in
      the build context), add the profile to `.env.example`
      `COMPOSE_PROFILES`, and add Makefile targets. Verify: `docker compose
      --profile       supply_chain config` is valid and `docker compose --profile
      supply_chain up --build` reaches "Agent ready" for all members. The
      `.env.example` also has `SUPPLY_CHAIN_L9_ENABLED=false` (the default
      everywhere, N31), passed to all five services (D12); with `false` the
      services start and refuse L9.
      Status: files and `config` check done. You rebuilt the stack with
      `docker compose up -d --build` on 2026-10-28 and reported that everything
      works (the profile comes from `COMPOSE_PROFILES` in `.env`, so
      `--profile` is not needed).
- [x] 7.2 Add integration tests (`tests/integration/test_supply_chain_*.py`
      health checks, `conftest.py` AGENTS entries) and an LLM flow test
      (`tests/integration/llm/test_supply_chain_flows.py`) that runs one
      case per configuration end to end and asserts that a record and a
      verdict were produced, without asserting PASS. It also asserts that
      every step's addressees each replied exactly once. Verify: the suites
      pass locally with SLIM up, and `tests/README.md` is updated.
      Status: health tests (8) and the two baseline flow runs pass with SLIM up
      (L9 cases skipped until 4.4 and 4.5); `tests/README.md` updated. Run them
      under another `COMPOSE_PROJECT_NAME` to protect a running stack (N30).
- [x] 7.3 Write `docs/supply_chain_commitment.md` (how to run, the cases,
      the configurations, the limits, reading the run files; link
      `docs/supply_chain_suggested_prompts.md` for the run types and
      prompts, and keep both consistent) and update the
      lungo `README.md` (TOC, topology, profiles, ports). Verify: `task
      links:check` and `task dashes:check` pass.
      Status: both pages written and cross-checked against the code; links and
      dashes were checked by script equivalents because `task links:check` and
      `task dashes:check` need bash 4 (macOS ships 3.2).

## 8. Helm, local cluster and CI

- [x] 8.1 Create the `supply-chain-buyer`, `supply-chain-supplier` and
      `supply-chain-logistics` charts by copying the logistics charts. The
      Buyer has `workflowApiUrl` and `workflowApiKey` and NodePort 30085;
      the supplier and logistics charts have no workflow API values. All
      three charts take `l9Enabled` (default false) and render it as
      `SUPPLY_CHAIN_L9_ENABLED`.
      Verify: `helm template` renders match the modified
      `agent-workflow-api-config` scenarios, and `l9Enabled=false` renders
      the variable as `false`.
      Status: `helm template` and `helm lint` pass for all three charts;
      `l9Enabled=false` renders `"false"`; the Buyer renders NodePort 30085 with
      `environment=local`; the workflow API keys appear only on the Buyer.
- [x] 8.2 Wire `local-cluster`: dependencies (supplier aliased three
      times), values (CORS, `VITE_SUPPLY_CHAIN_APP_API_URL`), overrides
      (SLIM targets, workflow API for the Buyer), the kind NodePort 30085,
      the version bump, and update the UI chart values and the
      `local-cluster/README.md`. Verify: `task helm:update-locks`, `task
      helm:check-locks` and `task helm:check-versions` pass.
      Status: `helm:update-locks` and `helm:check-versions` pass. `helm:check-locks`
      fails only because the new charts are not committed yet (it builds from
      git); rerun after the commit. The Go-template overrides were reviewed, not
      rendered (no `helmfile` here); aliases render as three releases.
- [x] 8.3 Add the three images to `/.github/workflows/docker-build-push.yaml`,
      the charts to `/.github/workflows/helm-push.yaml`, and the OASF dir
      to `scripts/push_oasf_records.sh` plus its bats test, and update
      `/docker/README.lungo.md`. Verify: `task workflows:lint`, `task
      workflows:check-permissions`, `task pins:check` and `task tests:bash`
      pass.
      Status: bats test passes (17); `workflows:check-permissions` passes;
      `workflows:lint` clean; `pins:check` and `tests:bash` could not run (bash 4
      needed), but no `uses:` or `FROM` line was added.

## 9. Integration and wrap-up

- [ ] 9.1 Headline pair first: run case `ambiguous` with `baseline` and then
      with `l9_hybrid`, on the same model and deployment, at least five
      times each (the baseline count may reuse task 4.3b). Then run the
      other three cases once per configuration. Save every run directory.
      Summarize in `docs/supply_chain_commitment_decisions.md` under a new
      "First observations" section: per case and configuration, the counts
      of silent failures, other failures, passes and invalid runs, whether
      L9 prevented the silent failure, and where it did not, what ACCORD
      did with "delivery". Report the counts, not one chosen run. Verify:
      the run directories exist and the table lists the counts per case and
      configuration.
- [ ] 9.2 Update `/CHANGELOG.md` and `/docs/TERMINOLOGY.md`, then run `task
      check:all`, `uv` lock sync and the full unit suite. Verify: all pass.
