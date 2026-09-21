#!/usr/bin/env bash
# Ensures every reference this repo makes to third-party code or images by a
# mutable, retargetable identifier (a Git tag/branch, a Docker image tag) is
# instead pinned to an immutable identifier (a full commit SHA, or an image
# digest), with the human-readable version it corresponds to kept nearby -
# protects against that tag being retargeted (moved, or force-pushed, or
# re-pushed to a new digest) silently changing what runs.
#
# Covers, today:
#   - `uses:` references to remote GitHub Actions/reusable workflows and
#     `docker://` actions in .github/workflows/*.y*ml
#   - `FROM` instructions in any Dockerfile
#   - `image:` fields in any docker-compose/compose file
#
# A line can opt out with a `# pin-exempt: <reason>` comment in place of the
# version comment, as long as it states a reason. When a new kind of
# floating reference shows up in this repo (a Terraform module source, an
# npm git dependency, ...), extend this script rather than leaving it
# uncovered - see .agents/rules/pinned-external-references.md.
#
# Usage: scripts/check_pinned_references.bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

failed=0

# Does $2 (the trailing text after the reference on the line) carry a
# `# pin-exempt: <reason>` comment? Prints an error and returns 1 if the
# comment is present but empty; returns 0 (exempt, nothing more to check)
# if present with a reason; returns 2 if no such comment is present at all.
check_exempt() {
  local file="$1" line_num="$2" trailing="$3"
  if [[ "$trailing" =~ \#[[:space:]]*pin-exempt:[[:space:]]*(.*)$ ]]; then
    local reason="${BASH_REMATCH[1]}"
    if [[ -z "${reason// /}" ]]; then
      echo "$file:$line_num: 'pin-exempt' comment must state a reason, e.g. '# pin-exempt: <why this can't be pinned>'"
      return 1
    fi
    return 0
  fi
  return 2
}

# --- .github/workflows/*.y*ml: `uses:` references -------------------------

shopt -s nullglob
workflow_files=(.github/workflows/*.yaml .github/workflows/*.yml)
shopt -u nullglob

for file in "${workflow_files[@]}"; do
  mapfile -t lines <"$file"
  line_num=0
  for line in "${lines[@]}"; do
    line_num=$((line_num + 1))

    case "$line" in
      *"uses:"*"./"*) continue ;; # local action/reusable workflow, nothing to pin
    esac

    if [[ "$line" =~ uses:[[:space:]]*docker://([^[:space:]]+)(.*)$ ]]; then
      ref="${BASH_REMATCH[1]}"
      trailing="${BASH_REMATCH[2]}"
      exempt_rc=0
      check_exempt "$file" "$line_num" "$trailing" || exempt_rc=$?
      case "$exempt_rc" in
        0) continue ;;
        1)
          failed=1
          continue
          ;;
      esac

      if [[ ! "$ref" =~ @sha256:[0-9a-f]{64}$ ]]; then
        echo "$file:$line_num: '$ref' is not pinned to an image digest - pin with '@sha256:<64-hex-digest>' (or add '# pin-exempt: <reason>')"
        failed=1
        continue
      fi
      if [[ ! "$ref" =~ :[^/@[:space:]]+@sha256: ]] && [[ ! "$trailing" =~ \#[[:space:]]*v?[0-9] ]]; then
        echo "$file:$line_num: digest-pinned but has no tag embedded and no version comment nearby (e.g. '# 3.19')"
        failed=1
      fi
      continue
    fi

    if [[ "$line" =~ uses:[[:space:]]*([A-Za-z0-9_.-]+/[A-Za-z0-9_./-]+)@([^[:space:]]+)(.*)$ ]]; then
      ref="${BASH_REMATCH[2]}"
      trailing="${BASH_REMATCH[3]}"

      exempt_rc=0
      check_exempt "$file" "$line_num" "$trailing" || exempt_rc=$?
      case "$exempt_rc" in
        0) continue ;;
        1)
          failed=1
          continue
          ;;
      esac

      if [[ ! "$ref" =~ ^[0-9a-f]{40}$ ]]; then
        echo "$file:$line_num: '$ref' is not a full commit SHA - pin to a 40-character hex commit SHA, not a tag or branch (or add '# pin-exempt: <reason>' if it genuinely can't be)"
        failed=1
        continue
      fi

      if [[ ! "$trailing" =~ \#[[:space:]]*v?[0-9] ]]; then
        echo "$file:$line_num: SHA-pinned but missing a version comment nearby (e.g. '# v4.4.0')"
        failed=1
      fi
    fi
  done
done

# --- Dockerfiles: `FROM` instructions --------------------------------------

mapfile -t dockerfiles < <(find . -type f \( -name "Dockerfile" -o -name "Dockerfile.*" -o -name "*.Dockerfile" \) -not -path "*/.git/*")

for file in "${dockerfiles[@]}"; do
  stage_names=()
  mapfile -t lines <"$file"
  line_num=0
  for line in "${lines[@]}"; do
    line_num=$((line_num + 1))

    if [[ "$line" =~ ^[[:space:]]*[Ff][Rr][Oo][Mm][[:space:]]+(--platform=[^[:space:]]+[[:space:]]+)?([^[:space:]]+)([[:space:]]+[Aa][Ss][[:space:]]+([^[:space:]]+))?(.*)$ ]]; then
      ref="${BASH_REMATCH[2]}"
      stage_name="${BASH_REMATCH[4]}"
      trailing="${BASH_REMATCH[5]}"

      is_prior_stage=0
      for s in "${stage_names[@]}"; do
        [[ "$s" == "$ref" ]] && is_prior_stage=1 && break
      done
      [ -n "$stage_name" ] && stage_names+=("$stage_name")

      if [ "$is_prior_stage" -eq 1 ] || [ "$ref" = "scratch" ]; then
        continue
      fi

      exempt_rc=0
      check_exempt "$file" "$line_num" "$trailing" || exempt_rc=$?
      case "$exempt_rc" in
        0) continue ;;
        1)
          failed=1
          continue
          ;;
      esac

      if [[ ! "$ref" =~ @sha256:[0-9a-f]{64}$ ]]; then
        echo "$file:$line_num: '$ref' is not pinned to an image digest - pin with '@sha256:<64-hex-digest>' (or add '# pin-exempt: <reason>')"
        failed=1
        continue
      fi
      if [[ ! "$ref" =~ :[^/@[:space:]]+@sha256: ]] && [[ ! "$trailing" =~ \#[[:space:]]*v?[0-9] ]]; then
        echo "$file:$line_num: digest-pinned but has no tag embedded and no version comment nearby (e.g. '# 20.11.0')"
        failed=1
      fi
    fi
  done
done

# --- docker-compose/compose files: `image:` fields -------------------------

mapfile -t compose_files < <(find . -type f \( -name "docker-compose*.yml" -o -name "docker-compose*.yaml" -o -name "compose.yml" -o -name "compose.yaml" \) -not -path "*/.git/*")

for file in "${compose_files[@]}"; do
  mapfile -t lines <"$file"
  line_num=0
  for line in "${lines[@]}"; do
    line_num=$((line_num + 1))

    if [[ "$line" =~ ^[[:space:]]*image:[[:space:]]*[\"\']?([^[:space:]\"\']+)[\"\']?(.*)$ ]]; then
      ref="${BASH_REMATCH[1]}"
      trailing="${BASH_REMATCH[2]}"

      exempt_rc=0
      check_exempt "$file" "$line_num" "$trailing" || exempt_rc=$?
      case "$exempt_rc" in
        0) continue ;;
        1)
          failed=1
          continue
          ;;
      esac

      if [[ ! "$ref" =~ @sha256:[0-9a-f]{64}$ ]]; then
        echo "$file:$line_num: '$ref' is not pinned to an image digest - pin with '@sha256:<64-hex-digest>' (or add '# pin-exempt: <reason>')"
        failed=1
        continue
      fi
      if [[ ! "$ref" =~ :[^/@[:space:]]+@sha256: ]] && [[ ! "$trailing" =~ \#[[:space:]]*v?[0-9] ]]; then
        echo "$file:$line_num: digest-pinned but has no tag embedded and no version comment nearby (e.g. '# 1.27.3')"
        failed=1
      fi
    fi
  done
done

if [ "$failed" -ne 0 ]; then
  exit 1
fi
echo "All action, reusable-workflow, and image references are pinned (digest/SHA, with a version kept nearby)."
