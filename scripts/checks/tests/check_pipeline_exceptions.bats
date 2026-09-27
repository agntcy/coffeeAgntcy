#!/usr/bin/env bats
# Mocked end-to-end test for check_pipeline_exceptions.bash: the script
# computes its own REPO_ROOT from BASH_SOURCE and cd's there before
# globbing .agents/skills/*/SKILL.md and .agents/skills/*/*/SKILL.md, so
# it's exercised here via the fixture-copy trick - a real copy of the
# script dropped into a throwaway fixture tree at the same relative
# depth (scripts/checks/), with fake SKILL.md files planted underneath
# it instead of touching this repo's real .agents/skills/ tree.
#
# RULE_ONLY_EXCEPTIONS is hardcoded inside the script itself, so these
# fixtures reuse rule names that are actually in that array today
# (pre-finalize-checks, alphabetize-entity-lists) rather than invented
# ones.

FIXTURE_REPO="$BATS_TEST_TMPDIR/repo"

setup() {
    mkdir -p "$FIXTURE_REPO/scripts/checks"
    cp "$BATS_TEST_DIRNAME/../check_pipeline_exceptions.bash" \
        "$FIXTURE_REPO/scripts/checks/check_pipeline_exceptions.bash"
    chmod +x "$FIXTURE_REPO/scripts/checks/check_pipeline_exceptions.bash"
    SCRIPT="$FIXTURE_REPO/scripts/checks/check_pipeline_exceptions.bash"
}

@test "passes clean when no skill mentions an exception-listed rule as its underlying rule" {
    mkdir -p "$FIXTURE_REPO/.agents/skills/clean-skill"
    cat >"$FIXTURE_REPO/.agents/skills/clean-skill/SKILL.md" <<'EOF'
---
name: clean-skill
---

# Clean skill

See [the dashes rule](../../rules/quality/check-dashes.md) - the underlying
rule for this skill.
EOF

    run "$SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"OK: every rule-only exception"* ]]
}

@test "fails, naming the rule, when a skill cross-links an exception-listed rule as its underlying rule" {
    mkdir -p "$FIXTURE_REPO/.agents/skills/quality-checks/bar-skill"
    cat >"$FIXTURE_REPO/.agents/skills/quality-checks/bar-skill/SKILL.md" <<'EOF'
---
name: bar-skill
---

# Bar skill

See [pre-finalize checks](../../../rules/quality/pre-finalize-checks.md).

This is the underlying rule for this skill.
EOF

    run "$SCRIPT"
    [ "$status" -eq 1 ]
    [[ "$output" == *"'pre-finalize-checks' is listed in repo-operation-pipeline.md's rule-only exceptions"* ]]
    [[ "$output" == *".agents/skills/quality-checks/bar-skill/SKILL.md names it as an underlying rule"* ]]
}

@test "does not false-positive on a skill that merely mentions exception rule filenames in passing" {
    mkdir -p "$FIXTURE_REPO/.agents/skills/repo-tooling/baz-skill"
    cat >"$FIXTURE_REPO/.agents/skills/repo-tooling/baz-skill/SKILL.md" <<'EOF'
---
name: baz-skill
---

# Baz skill

When finishing a repo operation, also apply the alphabetize-entity-lists.md and
pre-finalize-checks.md rules to keep things tidy.

This skill's own underlying rule is add-repo-operation.md, a different rule
entirely.
EOF

    run "$SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"OK: every rule-only exception"* ]]
}

@test "checks both flat and category-nested skill directory depths" {
    mkdir -p "$FIXTURE_REPO/.agents/skills/flat-skill"
    cat >"$FIXTURE_REPO/.agents/skills/flat-skill/SKILL.md" <<'EOF'
---
name: flat-skill
---

# Flat skill

Links to [organize large collections](../../rules/quality/organize-large-collections.md).

This is the underlying rule for this skill.
EOF

    run "$SCRIPT"
    [ "$status" -eq 1 ]
    [[ "$output" == *"'organize-large-collections' is listed"* ]]
}

@test "reports every offending skill, not just the first" {
    mkdir -p "$FIXTURE_REPO/.agents/skills/one-skill"
    cat >"$FIXTURE_REPO/.agents/skills/one-skill/SKILL.md" <<'EOF'
---
name: one-skill
---

Links to [keep docs consistent](../../rules/quality/keep-docs-consistent.md).

This is the underlying rule for this skill.
EOF

    mkdir -p "$FIXTURE_REPO/.agents/skills/two-skill"
    cat >"$FIXTURE_REPO/.agents/skills/two-skill/SKILL.md" <<'EOF'
---
name: two-skill
---

Links to [plan with openspec](../../rules/meta/plan-with-openspec.md).

This is the underlying rule for this skill.
EOF

    run "$SCRIPT"
    [ "$status" -eq 1 ]
    [[ "$output" == *"'keep-docs-consistent' is listed"* ]]
    [[ "$output" == *"'plan-with-openspec' is listed"* ]]
}
