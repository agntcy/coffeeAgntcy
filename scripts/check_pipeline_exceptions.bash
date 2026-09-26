#!/usr/bin/env bash
# Audits .agents/rules/repo-operation-pipeline.md's "Known exceptions"
# list: for each rule listed as a pure judgment-call exception (no
# script/task/skill/CI layer at all), confirms no skill under
# .agents/skills/ has grown into being that rule's own entry point. A
# rule that's quietly gained one without being promoted out of the
# exception list means the list is now lying about that rule's status.
#
# Signal: a skill genuinely IS the entry point for a rule when its
# SKILL.md has a markdown link ending in that rule's filename
# ("...<rule>.md)") within a couple of lines before the phrase
# "underlying rule" - the exact cross-link convention every checking-*/
# linting-* skill already follows (see e.g.
# .agents/skills/checking-dashes/SKILL.md). Deliberately narrower than
# "the filename appears near that phrase": .agents/skills/
# add-repo-operation/SKILL.md mentions alphabetize-entity-lists.md and
# pre-finalize-checks.md in passing (telling agents to also apply those
# rules) without being either one's own skill, and this script's own
# accompanying skill (auditing-pipeline-exceptions) explains this exact
# mechanism using both the trigger phrase and example rule names close
# together in prose - neither uses an actual markdown link ending in
# "<rule>.md)", so requiring that closing-paren shape is what tells a
# real cross-link apart from prose that merely discusses one.
#
# Keep this list in sync with the "Purely manual/visual conventions"
# bullet in .agents/rules/repo-operation-pipeline.md's "Known
# exceptions" section.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT" || exit 2

RULE_ONLY_EXCEPTIONS=(
    alphabetize-entity-lists
    file-tree-comment-alignment
    keep-docs-consistent
    organize-large-collections
    plan-with-openspec
    pre-finalize-checks
    self-review-after-change
)

failed=0

for rule in "${RULE_ONLY_EXCEPTIONS[@]}"; do
    for skill_file in .agents/skills/*/SKILL.md; do
        [[ -f "$skill_file" ]] || continue
        if grep -B2 "underlying rule" "$skill_file" 2>/dev/null | grep -qE "${rule}\.md\)"; then
            echo "error: '${rule}' is listed in repo-operation-pipeline.md's rule-only exceptions, but ${skill_file} names it as an underlying rule - promote it out of the exception list (add task/skill/CI layers), or update that skill's cross-link if this is itself a mistake."
            failed=1
        fi
    done
done

if [[ "$failed" -eq 0 ]]; then
    echo "OK: every rule-only exception in repo-operation-pipeline.md still has no skill of its own."
fi

exit "$failed"
