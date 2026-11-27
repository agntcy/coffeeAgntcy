#!/usr/bin/env bash
# Fails when any pin in scripts/lib/versions.sh has a second copy: a
# literal Node, uv, or Helm install, an image digest, an engines.node
# floor, a doc sentence, an npm lockfile version, or an OpenSpec skill
# stamp that disagrees, an install of a setup.sh-only tool outside
# scripts/setup.sh, or a scripts/lib/checksums.txt that does not hold
# exactly one checksum per archive URL the pins produce.
#
# One function per versions.sh pin. Node, uv, Helm, the npm tools, the
# OpenSpec skill stamps, and the tools that are installed only by setup.sh.
# check_pytest_pins covers the Python test workflow, which exports both
# NODE_VERSION and UV_VERSION for docker compose.
#
# Usage: scripts/checks/check_versions.bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

# shellcheck source=scripts/lib/versions.sh
source "$REPO_ROOT/scripts/lib/versions.sh"

NODE_IMAGE_FILE="scripts/lib/node-image.txt"
UV_IMAGE_FILE="scripts/lib/uv-image.txt"
HELM_WORKFLOW=".github/workflows/helm-package-reusable.yaml"
NPM_LOCK="scripts/lib/npm-tools/package-lock.json"
# Literal markdown backticks, and the ${NODE_VERSION} text callers write.
# Neither is a shell expansion. shellcheck disable applies to the next command.
# shellcheck disable=SC2016
MARKER='(`NODE_VERSION` in `scripts/lib/versions.sh`)'
# shellcheck disable=SC2016
NODE_EXPANSION='${NODE_VERSION}'
DOC_FILES=(
    "TUTORIAL.md"
    "coffeeAGNTCY/coffee_agents/corto/README.md"
    "coffeeAGNTCY/coffee_agents/lungo/README.md"
    "coffeeAGNTCY/coffee_agents/corto/exchange/frontend/README.md"
    "coffeeAGNTCY/coffee_agents/lungo/frontend/README.md"
)

ENGINE_FILES=(
    "coffeeAGNTCY/coffee_agents/corto/exchange/frontend/package.json"
    "coffeeAGNTCY/coffee_agents/corto/exchange/frontend/package-lock.json"
    "coffeeAGNTCY/coffee_agents/lungo/frontend/package.json"
    "coffeeAGNTCY/coffee_agents/lungo/frontend/package-lock.json"
)

failed=0

report() {
    echo "$*" >&2
    failed=1
}

# Prints every line of a file except full-line comments. Inline comments
# stay: stripping from # on would break ${HELM_VERSION#v}. A whole-file
# grep goes through this, so a comment cannot satisfy or trip a check.
active_lines() {
    grep -Ev '^[[:space:]]*#' "$1" || true
}

# has_active <file> <grep flag letters> <pattern>: succeeds when a
# non-comment line of the file matches. The text goes through a variable,
# not a pipe, because grep -q closing early would fail a pipefail pipeline.
has_active() {
    local file="$1" flags="$2" pattern="$3" text
    text="$(active_lines "$file")"
    grep -q"$flags" -- "$pattern" <<<"$text"
}

# check_action_version_input <file> <action> <input key> <VAR> <label> [forbidden key]
# Every step that uses <action> in the workflow file must pass its <key>
# input as ${{ env.VAR }} or ${{ steps.X.outputs.Y }}. A missing input, a
# literal, any other expression, or the forbidden key (for example
# node-version-file) fails. Steps are buffered, so an inline flow mapping,
# a with: block before uses:, and a quoted action all count. Comment lines
# are skipped and the action name is matched without regard to case.
check_action_version_input() {
    local file="$1" action="$2" key="$3" var="$4" label="$5" forbid="${6:-}" msg
    while IFS= read -r msg; do
        [[ -n "$msg" ]] && report "$msg"
    done < <(awk -v action="$action" -v key="$key" -v var="$var" -v label="$label" -v forbid="$forbid" -v q="'" '
        BEGIN {
            allowed = "^\\$\\{\\{[[:space:]]*(steps\\.[A-Za-z0-9_-]+\\.outputs\\.[A-Za-z0-9_-]+|env\\." var ")[[:space:]]*\\}\\}"
            literal = "^[\"" q "]?v?[0-9]"
            keyre = "(^|[^A-Za-z0-9_-])" key ":[[:space:]]*"
            usesre = "uses:[[:space:]]*[\"" q "]?" tolower(action) "@"
            step_indent = -1
        }
        function flush_step() {
            if (has_action) {
                if (has_forbid) {
                    print FILENAME " uses " forbid " for " action " instead of " var ". Source scripts/lib/versions.sh and pass " var "."
                } else if (!has_key) {
                    print FILENAME " calls " action " without a " key " input. Pass " var " from scripts/lib/versions.sh."
                } else if (value !~ allowed) {
                    if (value ~ literal) {
                        print FILENAME " sets " label " to a literal. Source scripts/lib/versions.sh and pass " var "."
                    } else {
                        print FILENAME " sets " label " to something other than " var ". Source scripts/lib/versions.sh and pass " var "."
                    }
                }
            }
            has_action = 0; has_key = 0; has_forbid = 0; value = ""; step_indent = -1
        }
        /^[[:space:]]*#/ || /^[[:space:]]*$/ { next }
        {
            match($0, /^[[:space:]]*/)
            indent = RLENGTH
            if ($0 ~ /^[[:space:]]*-[[:space:]]/ && (step_indent < 0 || indent <= step_indent)) {
                flush_step()
                step_indent = indent
            } else if (step_indent >= 0 && indent <= step_indent) {
                flush_step()
            }
            if (step_indent >= 0) {
                if (tolower($0) ~ usesre) has_action = 1
                if (forbid != "" && index($0, forbid ":") > 0) has_forbid = 1
                if (match($0, keyre)) {
                    has_key = 1
                    value = substr($0, RSTART + RLENGTH)
                }
            }
        }
        END { flush_step() }
    ' "$file")
}

first_node_semver() {
    local file="$1" line
    while IFS= read -r line || [[ -n "$line" ]]; do
        # The install sentence has Node.js, a semver, and " or higher". An
        # earlier versionless Node.js mention is not the sentence.
        if [[ "$line" == *"Node.js"* && "$line" == *" or higher"* && "$line" =~ [0-9]+\.[0-9]+\.[0-9]+ ]]; then
            printf '%s' "${BASH_REMATCH[0]}"
            return 0
        fi
    done <"$file"
    return 1
}

first_node_engine() {
    local file="$1" line
    while IFS= read -r line || [[ -n "$line" ]]; do
        # The root floor comes before the first dependency. Past that point
        # a match would be a dependency's engines.node, not ours.
        [[ "$line" == *'"node_modules/'* ]] && return 1
        if [[ "$line" =~ \"node\":[[:space:]]*\"(>=[0-9]+\.[0-9]+\.[0-9]+)\" ]]; then
            printf '%s' "${BASH_REMATCH[1]}"
            return 0
        fi
    done <"$file"
    return 1
}

read_record() {
    RECORD_VERSION=""
    RECORD_DIGEST=""
    [[ -f "$NODE_IMAGE_FILE" ]] || {
        report "$NODE_IMAGE_FILE is missing"
        return 1
    }
    local line count=0 version digest
    while IFS= read -r line || [[ -n "$line" ]]; do
        [[ "$line" =~ ^# ]] && continue
        [[ -z "$line" ]] && continue
        if [[ "$line" =~ ^([0-9]+\.[0-9]+\.[0-9]+)[[:space:]]+(sha256:[0-9a-f]{64})$ ]]; then
            version="${BASH_REMATCH[1]}"
            digest="${BASH_REMATCH[2]}"
            count=$((count + 1))
        else
            report "$NODE_IMAGE_FILE has a line that is not '<version> sha256:<64-hex>': $line"
            return 1
        fi
    done <"$NODE_IMAGE_FILE"
    if [[ "$count" -ne 1 ]]; then
        report "$NODE_IMAGE_FILE must contain exactly one digest line"
        return 1
    fi
    RECORD_VERSION="$version"
    RECORD_DIGEST="$digest"
}

check_workflows() {
    local file line
    [[ -d .github/workflows ]] || {
        report ".github/workflows is missing"
        return 0
    }
    while IFS= read -r file; do
        [[ -n "$file" ]] || continue
        if has_active "$file" E '(node-version:|uses:[[:space:]]*["'\'']?[Aa]ctions/setup-node@)'; then
            check_action_version_input "$file" actions/setup-node node-version NODE_VERSION node-version node-version-file
            if ! has_active "$file" F 'scripts/lib/versions.sh'; then
                report "$file sets node-version without sourcing scripts/lib/versions.sh"
            fi
            if ! has_active "$file" F 'NODE_VERSION'; then
                report "$file sets node-version without reading NODE_VERSION"
            fi
        fi
        # A version manager at a literal version is a second Node install.
        if has_active "$file" E '(^|[^A-Za-z0-9_-])(nvm|fnm|asdf|volta)[[:space:]]+(install|use)[[:space:]]+(node[[:space:]@]+)?["'\'']?v?[0-9]'; then
            report "$file installs Node through a version manager at a literal version. Read NODE_VERSION from scripts/lib/versions.sh."
        fi
    done < <(find .github/workflows -type f \( -name '*.yml' -o -name '*.yaml' \) -not -path '*/node_modules/*' | sort)
}

check_images() {
    local digest="$1" file line found
    # FROM may carry flags (--platform=...) and a registry prefix, and a
    # compose image: line may be quoted.
    local node_image_re='^[[:space:]]*([Ff][Rr][Oo][Mm][[:space:]]+(--[^[:space:]]+[[:space:]]+)*|image:[[:space:]]*["'\'']?)(docker\.io/)?(library/)?node[:@]'
    while IFS= read -r file; do
        [[ -n "$file" ]] || continue
        found=0
        while IFS= read -r line || [[ -n "$line" ]]; do
            [[ "$line" =~ $node_image_re ]] || continue
            found=1
            if [[ "$line" =~ node:[0-9] ]]; then
                report "$file pins a numeric node image tag. Use ${NODE_EXPANSION} from scripts/lib/versions.sh."
            elif [[ "$line" != *"$NODE_EXPANSION"* ]]; then
                report "$file has a node image that does not use ${NODE_EXPANSION}"
            fi
            # Only the UI image carries the recorded Alpine digest. Another
            # Node image (a different variant) has its own digest, and
            # pins:check already requires it to be immutable.
            if [[ "${file#./}" == "docker/Dockerfile.ui" ]]; then
                if [[ "$line" =~ @(sha256:[0-9a-f]{64}) ]]; then
                    if [[ "${BASH_REMATCH[1]}" != "$digest" ]]; then
                        report "$file digest ${BASH_REMATCH[1]} does not match $NODE_IMAGE_FILE ($digest)"
                    fi
                else
                    report "$file node image has no @sha256 digest"
                fi
            fi
        done <"$file"
        if [[ "${file#./}" == "docker/Dockerfile.ui" && "$found" -eq 0 ]]; then
            report "docker/Dockerfile.ui does not install node from NODE_VERSION"
        fi
    done < <(find . -type f \( -name 'Dockerfile' -o -name 'Dockerfile.*' -o -name '*.Dockerfile' -o -name 'docker-compose*.yml' -o -name 'docker-compose*.yaml' -o -name 'compose.yml' -o -name 'compose.yaml' \) -not -path '*/.git/*' -not -path '*/node_modules/*' -not -path '*/.tools/*' | sort)
}

# check_compose_args <file> <dockerfile> <VAR>
# Every build: block of a compose file that names <dockerfile> must pass
# <VAR> as a build arg through ${VAR:?...}, so a missing variable fails
# the build instead of falling back to a second copy. A default (:- or
# :=) or a literal anywhere in the file's active lines fails too. Blocks
# are matched one by one, so a service that leaves the arg out is named
# even when another service in the same file has it.
check_compose_args() {
    local file="$1" dockerfile="$2" var="$3" msg
    has_active "$file" F "$dockerfile" || return 0
    if has_active "$file" E "\\\$\\{${var}:?[-=]|${var}[[:space:]]*[=:][[:space:]]*[\"']?v?[0-9]"; then
        report "$file gives $var a default or a literal. Pass it with \${$var:?...} only."
    fi
    while IFS= read -r msg; do
        [[ -n "$msg" ]] && report "$msg"
    done < <(awk -v df="$dockerfile" -v var="$var" '
        function flush_block() {
            if (in_build && has_df) {
                if (!has_var) print FILENAME ":" build_line " builds " df " without passing " var
                else if (!has_guard) print FILENAME ":" build_line " passes " var " without ${" var ":?...}"
            }
            in_build = 0; has_df = 0; has_var = 0; has_guard = 0
        }
        /^[[:space:]]*#/ || /^[[:space:]]*$/ { next }
        {
            match($0, /^[[:space:]]*/)
            indent = RLENGTH
            if (in_build && indent <= build_indent) flush_block()
            if (!in_build && $0 ~ /^[[:space:]]*build:[[:space:]]*$/) {
                in_build = 1; build_indent = indent; build_line = NR
                next
            }
            if (in_build) {
                if (index($0, "dockerfile:") > 0 && index($0, df) > 0) has_df = 1
                if ($0 ~ (var "[[:space:]]*(:|=)")) {
                    has_var = 1
                    if (index($0, "${" var ":?") > 0) has_guard = 1
                }
            }
        }
        END { flush_block() }
    ' "$file")
}

check_ui_callers() {
    local file
    while IFS= read -r file; do
        [[ -n "$file" ]] || continue
        check_compose_args "$file" docker/Dockerfile.ui NODE_VERSION
    done < <(find . -type f \( -name 'docker-compose*.yml' -o -name 'docker-compose*.yaml' -o -name 'compose.yml' -o -name 'compose.yaml' \) -not -path '*/.git/*' -not -path '*/node_modules/*' -not -path '*/.tools/*' | sort)

    local reusable=".github/workflows/docker-build-reusable.yaml"
    if [[ ! -f "$reusable" ]]; then
        report "$reusable is missing; CI UI builds must inject NODE_VERSION"
        return 0
    fi
    if ! has_active "$reusable" F 'scripts/lib/versions.sh'; then
        report "$reusable does not source scripts/lib/versions.sh"
    fi
    if ! has_active "$reusable" F 'docker/Dockerfile.ui'; then
        report "$reusable does not limit the Node build-arg to docker/Dockerfile.ui"
    fi
    if ! has_active "$reusable" F "NODE_VERSION=$NODE_EXPANSION"; then
        report "$reusable does not pass NODE_VERSION from scripts/lib/versions.sh"
    fi
    if has_active "$reusable" E 'NODE_VERSION=["'\'']?v?[0-9]'; then
        report "$reusable assigns NODE_VERSION a literal"
    fi
}

check_setup() {
    local setup="scripts/setup.sh"
    if [[ ! -f "$setup" ]]; then
        report "$setup is missing"
        return 0
    fi
    # shellcheck disable=SC2016
    if ! has_active "$setup" F '$NODE_VERSION' && ! has_active "$setup" F '${NODE_VERSION}'; then
        report "$setup no longer installs Node from NODE_VERSION"
    fi
    if has_active "$setup" E 'node-v[0-9]'; then
        report "$setup hardcodes a node-v<version> directory"
    fi
}

check_engines() {
    local file got
    for file in "${ENGINE_FILES[@]}"; do
        if [[ ! -f "$file" ]]; then
            report "$file is missing"
            continue
        fi
        if ! got="$(first_node_engine "$file")"; then
            report "$file has no root engines.node floor"
            continue
        fi
        if [[ "$got" != ">=$NODE_VERSION" ]]; then
            report "$file engines.node is $got, want >=$NODE_VERSION"
        fi
    done
}

check_docs() {
    local file got
    for file in "${DOC_FILES[@]}"; do
        if [[ ! -f "$file" ]]; then
            report "$file is missing"
            continue
        fi
        if ! got="$(first_node_semver "$file")"; then
            report "$file has no Node.js install sentence"
            continue
        fi
        if [[ "$got" != "$NODE_VERSION" ]]; then
            report "$file states Node.js $got, NODE_VERSION is $NODE_VERSION"
        fi
        if ! grep -Fq "$MARKER" "$file"; then
            report "$file Node.js sentence does not name NODE_VERSION in scripts/lib/versions.sh"
        fi
    done
}

check_node() {
    if ! read_record; then
        return 0
    fi
    if [[ "$RECORD_VERSION" != "$NODE_VERSION" ]]; then
        report "$NODE_IMAGE_FILE records $RECORD_VERSION, NODE_VERSION is $NODE_VERSION"
    fi
    check_workflows
    check_images "$RECORD_DIGEST"
    check_ui_callers
    check_setup
    check_engines
    check_docs
}

# shellcheck disable=SC2016
UV_EXPANSION='${UV_VERSION}'
check_uv_record() {
    UV_RECORD_VERSION=""
    UV_RECORD_DIGEST=""
    [[ -f "$UV_IMAGE_FILE" ]] || {
        report "$UV_IMAGE_FILE is missing"
        return 1
    }
    local line count=0 version digest
    while IFS= read -r line || [[ -n "$line" ]]; do
        [[ "$line" =~ ^# ]] && continue
        [[ -z "$line" ]] && continue
        if [[ "$line" =~ ^([0-9]+\.[0-9]+\.[0-9]+)[[:space:]]+(sha256:[0-9a-f]{64})$ ]]; then
            version="${BASH_REMATCH[1]}"
            digest="${BASH_REMATCH[2]}"
            count=$((count + 1))
        else
            report "$UV_IMAGE_FILE has a line that is not '<version> sha256:<64-hex>': $line"
            return 1
        fi
    done <"$UV_IMAGE_FILE"
    if [[ "$count" -ne 1 ]]; then
        report "$UV_IMAGE_FILE must contain exactly one digest line"
        return 1
    fi
    UV_RECORD_VERSION="$version"
    UV_RECORD_DIGEST="$digest"
}

check_uv() {
    if ! check_uv_record; then
        return 0
    fi
    if [[ "$UV_RECORD_VERSION" != "$UV_VERSION" ]]; then
        report "$UV_IMAGE_FILE records $UV_RECORD_VERSION, UV_VERSION is $UV_VERSION"
    fi
    local file="docker/Dockerfile.python-agent" line found=0
    if [[ ! -f "$file" ]]; then
        report "$file is missing"
        return 0
    fi
    while IFS= read -r line || [[ -n "$line" ]]; do
        [[ "$line" =~ ^[[:space:]]*FROM[[:space:]]+astral/uv: ]] || continue
        found=1
        if [[ "$line" =~ uv:[0-9] ]]; then
            report "$file pins a numeric uv image tag. Use ${UV_EXPANSION} from scripts/lib/versions.sh."
        elif [[ "$line" != *"$UV_EXPANSION"* ]]; then
            report "$file has a uv image that does not use ${UV_EXPANSION}"
        fi
        if [[ "$line" =~ @(sha256:[0-9a-f]{64}) ]]; then
            if [[ "${BASH_REMATCH[1]}" != "$UV_RECORD_DIGEST" ]]; then
                report "$file digest ${BASH_REMATCH[1]} does not match $UV_IMAGE_FILE ($UV_RECORD_DIGEST)"
            fi
        else
            report "$file uv image has no @sha256 digest"
        fi
    done <"$file"
    if [[ "$found" -eq 0 ]]; then
        report "$file does not install uv from UV_VERSION"
    fi

    while IFS= read -r file; do
        [[ -n "$file" ]] || continue
        check_compose_args "$file" docker/Dockerfile.python-agent UV_VERSION
    done < <(find . -type f \( -name 'docker-compose*.yml' -o -name 'docker-compose*.yaml' -o -name 'compose.yml' -o -name 'compose.yaml' \) -not -path '*/.git/*' -not -path '*/node_modules/*' -not -path '*/.tools/*' | sort)

    local reusable=".github/workflows/docker-build-reusable.yaml"
    if [[ ! -f "$reusable" ]]; then
        report "$reusable is missing; CI Python image builds must inject UV_VERSION"
        return 0
    fi
    if ! has_active "$reusable" F 'docker/Dockerfile.python-agent'; then
        report "$reusable does not limit the uv build-arg to docker/Dockerfile.python-agent"
    fi
    if ! has_active "$reusable" F "UV_VERSION=$UV_EXPANSION"; then
        report "$reusable does not pass UV_VERSION from scripts/lib/versions.sh"
    fi
    if has_active "$reusable" E 'UV_VERSION=["'\'']?v?[0-9]'; then
        report "$reusable assigns UV_VERSION a literal"
    fi
}

# astral-sh/setup-uv installs the uv CLI that CI runs. Without a version
# input it picks its own, so every use passes UV_VERSION, either from the
# job env or from an earlier step's output, and the workflow exports it
# from versions.sh first.
check_setup_uv() {
    local file line in_step ok msg
    local version_re='version:[[:space:]]*\$\{\{[[:space:]]*(env\.UV_VERSION|steps\.[A-Za-z0-9_-]+\.outputs\.UV_VERSION)[[:space:]]*\}\}'
    msg=" sets up uv without passing UV_VERSION. Export it from scripts/lib/versions.sh and pass version: \${{ env.UV_VERSION }} or \${{ steps.<id>.outputs.UV_VERSION }}."
    while IFS= read -r file; do
        [[ -n "$file" ]] || continue
        has_active "$file" E 'uses:[[:space:]]*astral-sh/setup-uv@' || continue
        if ! has_active "$file" F "UV_VERSION=$UV_EXPANSION"; then
            report "$file uses astral-sh/setup-uv without exporting UV_VERSION from scripts/lib/versions.sh"
        fi
        in_step=0
        ok=0
        while IFS= read -r line || [[ -n "$line" ]]; do
            [[ "$line" =~ ^[[:space:]]*# ]] && continue
            if [[ "$line" =~ ^[[:space:]]*-[[:space:]] ]]; then
                if [[ "$in_step" -eq 1 && "$ok" -eq 0 ]]; then
                    report "$file$msg"
                fi
                in_step=0
            fi
            if [[ "$line" =~ uses:[[:space:]]*astral-sh/setup-uv@ ]]; then
                in_step=1
                ok=0
            fi
            if [[ "$in_step" -eq 1 && "$line" =~ $version_re ]]; then
                ok=1
            fi
        done <"$file"
        if [[ "$in_step" -eq 1 && "$ok" -eq 0 ]]; then
            report "$file$msg"
        fi
    done < <(find .github/workflows -type f \( -name '*.yml' -o -name '*.yaml' \) -not -path '*/node_modules/*' 2>/dev/null | sort)
}

# pytest runs docker compose, which interpolates both pins. The test
# workflow has to export them from versions.sh or CI compose fails.
check_pytest_pins() {
    local tests=".github/workflows/test-reusable.yaml"
    if [[ ! -f "$tests" ]]; then
        report "$tests is missing; Python tests must export NODE_VERSION and UV_VERSION"
        return 0
    fi
    if ! has_active "$tests" E '^[[:space:]]*(\.|source)[[:space:]]+scripts/lib/versions\.sh'; then
        report "$tests does not source scripts/lib/versions.sh"
    fi
    if ! has_active "$tests" F "NODE_VERSION=$NODE_EXPANSION"; then
        report "$tests does not export NODE_VERSION from scripts/lib/versions.sh"
    fi
    if ! has_active "$tests" F "UV_VERSION=$UV_EXPANSION"; then
        report "$tests does not export UV_VERSION from scripts/lib/versions.sh"
    fi
    if has_active "$tests" E 'NODE_VERSION=["'\'']?v?[0-9]'; then
        report "$tests assigns NODE_VERSION a literal"
    fi
    if has_active "$tests" E 'UV_VERSION=["'\'']?v?[0-9]'; then
        report "$tests assigns UV_VERSION a literal"
    fi
}

check_helm() {
    if [[ ! -f "$HELM_WORKFLOW" ]]; then
        report "$HELM_WORKFLOW is missing"
        return 0
    fi
    if ! has_active "$HELM_WORKFLOW" F 'scripts/lib/versions.sh'; then
        report "$HELM_WORKFLOW does not source scripts/lib/versions.sh"
    fi
    if ! has_active "$HELM_WORKFLOW" F 'HELM_VERSION'; then
        report "$HELM_WORKFLOW does not read HELM_VERSION"
    fi
    # Only the azure/setup-helm step's version: input is the Helm pin.
    # Other actions (setup-buildx and the like) have their own version:
    # input. Every workflow is scanned, not only the Helm one.
    local file
    while IFS= read -r file; do
        [[ -n "$file" ]] || continue
        if has_active "$file" E 'HELM_VERSION[[:space:]]*[:=][[:space:]]*["'\'']?v?[0-9]'; then
            report "$file assigns HELM_VERSION a literal. Source scripts/lib/versions.sh."
        fi
        if has_active "$file" E 'uses:[[:space:]]*["'\'']?[Aa]zure/setup-helm@'; then
            check_action_version_input "$file" azure/setup-helm version HELM_VERSION "Helm version"
        fi
    done < <(find .github/workflows -type f \( -name '*.yml' -o -name '*.yaml' \) -not -path '*/node_modules/*' | sort)
}

check_npm_pins() {
    if [[ ! -f "$NPM_LOCK" ]]; then
        report "$NPM_LOCK is missing"
        return 0
    fi
    local line openspec_got="" renovate_got=""
    while IFS= read -r line || [[ -n "$line" ]]; do
        [[ "$line" == *'"node_modules/'* ]] && break
        if [[ "$line" =~ \"@fission-ai/openspec\":\ \"([^\"]+)\" ]]; then
            openspec_got="${BASH_REMATCH[1]}"
        fi
        if [[ "$line" =~ \"renovate\":\ \"([^\"]+)\" ]]; then
            renovate_got="${BASH_REMATCH[1]}"
        fi
    done <"$NPM_LOCK"
    if [[ -z "$openspec_got" ]]; then
        report "$NPM_LOCK has no root @fission-ai/openspec version"
    elif [[ "$openspec_got" != "$OPENSPEC_VERSION" ]]; then
        report "$NPM_LOCK openspec is $openspec_got, OPENSPEC_VERSION is $OPENSPEC_VERSION"
    fi
    if [[ -z "$renovate_got" ]]; then
        report "$NPM_LOCK has no root renovate version"
    elif [[ "$renovate_got" != "$RENOVATE_VERSION" ]]; then
        report "$NPM_LOCK renovate is $renovate_got, RENOVATE_VERSION is $RENOVATE_VERSION"
    fi
}

check_openspec_stamps() {
    [[ -d .agents/skills ]] || return 0
    local file line found
    while IFS= read -r file; do
        [[ -n "$file" ]] || continue
        found=0
        while IFS= read -r line || [[ -n "$line" ]]; do
            # Quoted, single-quoted, or bare. A missing stamp is reported below.
            if [[ "$line" =~ generatedBy:[[:space:]]*[\"\']?([^\"\'[:space:]]+)[\"\']? ]]; then
                found=1
                if [[ "${BASH_REMATCH[1]}" != "$OPENSPEC_VERSION" ]]; then
                    report "$file generatedBy is ${BASH_REMATCH[1]}, OPENSPEC_VERSION is $OPENSPEC_VERSION"
                fi
            fi
        done <"$file"
        [[ "$found" -eq 1 ]] || report "$file is missing a generatedBy stamp"
    done < <(find .agents/skills -type f -path '*/openspec-*/SKILL.md' | sort)
}

# join_continuations <file>: prints the file with every line that ends in a
# backslash joined to the next one, so "apt-get install -y \" followed by
# "shellcheck" is read as one command. A full-line comment is never joined,
# so a comment that ends in a backslash cannot swallow the line after it.
join_continuations() {
    awk '
        {
            if (buf == "" && $0 ~ /^[[:space:]]*#/) { print; next }
            if (sub(/[[:space:]]*\\[[:space:]]*$/, " ")) { buf = buf $0; next }
            print buf $0
            buf = ""
        }
        END { if (buf != "") print buf }
    ' "$1"
}

check_single_installs() {
    local setup="scripts/setup.sh" assets="scripts/lib/assets.sh" var file line action tool
    for var in ACTIONLINT_VERSION BATS_VERSION SHELLCHECK_VERSION SHFMT_VERSION TASK_VERSION; do
        if [[ ! -f "$setup" ]] || ! has_active "$setup" F "$var"; then
            report "$setup does not install from $var"
        fi
        if [[ ! -f "$assets" ]] || ! has_active "$assets" F "$var"; then
            report "$assets does not install from $var"
        fi
    done
    # Any install of these tools outside scripts/setup.sh is a second copy,
    # at any version: a package manager line naming the tool, or a download
    # of its installer or release.
    local tools='shellcheck|actionlint|shfmt|bats-core|bats|go-task|task'
    # Flags may sit between the manager and the verb (apt-get -y install,
    # apk --no-cache add).
    local pm_re="(apt-get|apt|apk|brew|dnf|yum|pip3?|pipx|npm|npx|go|cargo|snap|conda|mamba|gem|asdf|mise|choco|winget|scoop)[[:space:]]+(-[^[:space:]]+[[:space:]]+)*(install|add|i)[[:space:]]+(.*[[:space:]/@=])?($tools)([[:space:]@=:]|\$)"
    # A literal version assigned to any tool pin outside versions.sh.
    local literal_re='(^|[^A-Za-z0-9_])(ACTIONLINT|BATS|OPENSPEC|RENOVATE|SHELLCHECK|SHFMT|TASK|UV)_VERSION[[:space:]]*[:=][[:space:]]*["'\'']?v?[0-9]+\.[0-9]+'
    # A pre-commit repo that ships one of the tools brings its own copy.
    local hook_re='(^|[[:space:]-])repo:[[:space:]]*[^[:space:]]*(shellcheck|actionlint|shfmt|bats)'
    local download_re='taskfile\.dev/install\.sh|github\.com/(koalaman/shellcheck|rhysd/actionlint|mvdan/sh|bats-core/bats-core|go-task/task)/(releases|archive)'
    # A tool name directly followed by a version: joined by - _ @ : = / or
    # whitespace, with an optional -py suffix (shellcheck-py==0.10.0.1).
    # That covers release file names, image tags, tool@version, and
    # "shellcheck 0.10.0". A tool name and a semver that only share a line
    # (a step name that lists other versions, another tool's version) are
    # not a pin.
    local pinned_re='(shellcheck|actionlint|shfmt|bats-core|go-task/task)(-py)?[-_@:=/[:space:]]+[vV]?[0-9]+\.[0-9]+\.[0-9]+'
    while IFS= read -r file; do
        [[ -n "$file" ]] || continue
        while IFS= read -r line || [[ -n "$line" ]]; do
            # A comment that mentions an install is not an install.
            [[ "$line" =~ ^[[:space:]]*# ]] && continue
            # Nor is a trailing comment: "run: task lint # shellcheck 0.10.0"
            # and "uses: ./local-action # v1.2.3" are not installs either.
            line="${line%%[[:space:]]#*}"
            # An action for one of these tools brings its own copy, whatever
            # its tag or the case of its name. CI runs them through task
            # from scripts/setup.sh. A local ./ action is the repo's own.
            if [[ "$line" =~ (^|[[:space:]{,])uses:[[:space:]]*[\"\']?([^[:space:]\"\'@#,}]+) ]]; then
                action="$(printf '%s' "${BASH_REMATCH[2]}" | tr '[:upper:]' '[:lower:]')"
                if [[ "$action" != ./* && "$action" =~ (shellcheck|actionlint|shfmt|bats|go-task|setup-task) ]]; then
                    tool="${BASH_REMATCH[1]}"
                    [[ "$tool" == "setup-task" ]] && tool="task"
                    report "$file uses an action that installs ${tool}. Run it through task from scripts/setup.sh."
                    continue
                fi
            fi
            if [[ "$line" =~ $pm_re ]]; then
                report "$file installs ${BASH_REMATCH[5]} outside scripts/setup.sh. Run it through task from scripts/setup.sh."
                continue
            fi
            if [[ "$line" =~ $literal_re ]]; then
                report "$file assigns ${BASH_REMATCH[2]}_VERSION a literal. Read scripts/lib/versions.sh."
                continue
            fi
            if [[ "$line" =~ $hook_re ]]; then
                report "$file uses a pre-commit repo that installs ${BASH_REMATCH[2]}. Run it through task from scripts/setup.sh."
                continue
            fi
            if [[ "$line" =~ $download_re ]]; then
                report "$file downloads a toolchain tool outside scripts/setup.sh. Run it through task from scripts/setup.sh."
                continue
            fi
            if [[ "$line" =~ $pinned_re ]]; then
                report "$file installs a toolchain tool at a numeric version. Read scripts/lib/versions.sh."
            fi
        done < <(join_continuations "$file")
    done < <(find . \( -name .git -o -name node_modules -o -name .tools -o -name .venv \
        -o -path ./scripts/checks \) -prune -o -type f \
        \( -path './.github/workflows/*.yml' -o -path './.github/workflows/*.yaml' \
        -o -path './.github/actions/*.yml' -o -path './.github/actions/*.yaml' \
        -o -name 'Dockerfile' -o -name 'Dockerfile.*' -o -name '*.Dockerfile' \
        -o -name 'Taskfile*.yml' -o -name 'Taskfile*.yaml' \
        -o -name 'docker-compose*.yml' -o -name 'docker-compose*.yaml' \
        -o -name 'compose*.yml' -o -name 'compose*.yaml' \
        -o -name '.pre-commit-config.yaml' -o -name '.pre-commit-config.yml' \
        -o -path './scripts/*.sh' -o -path './scripts/*.bash' \) \
        -not -path ./scripts/setup.sh -not -path ./scripts/lib/assets.sh \
        -not -path ./scripts/lib/versions.sh -print 2>/dev/null | sort)
}

# scripts/lib/checksums.txt holds one SHA-256 per tool archive URL that
# scripts/lib/assets.sh builds from the pins. After a bump that skipped
# task tools:checksums, a full setup refuses the new archive and the old
# lines linger. The expected URLs come from assets.sh itself, so this
# check and the generator cannot disagree on the list.
check_checksums() {
    local assets="scripts/lib/assets.sh" sums="scripts/lib/checksums.txt"
    if [[ ! -f "$assets" ]]; then
        report "$assets is missing"
        return 0
    fi
    if [[ ! -f "$sums" ]]; then
        report "$sums is missing. Run task tools:checksums."
        return 0
    fi
    local expected recorded url
    # The subshell keeps assets.sh's names out of this script.
    expected="$(
        # shellcheck source=scripts/lib/assets.sh
        source "$assets"
        for tool in "${ASSET_TOOLS[@]}"; do
            for platform in "${SUPPORTED_PLATFORMS[@]}"; do
                asset_url "$tool" "${platform%-*}" "${platform#*-}"
            done
        done | LC_ALL=C sort -u
    )" || {
        report "$assets could not list the archive URLs for the pins"
        return 0
    }
    if [[ -z "$expected" ]]; then
        report "$assets lists no archive URLs"
        return 0
    fi
    # A line counts only with a 64-hex hash in front of the URL.
    recorded="$(awk '$1 ~ /^[0-9a-f]{64}$/ && NF == 2 { print $2 }' "$sums" | LC_ALL=C sort -u)"
    while IFS= read -r url; do
        [[ -n "$url" ]] || continue
        report "$sums has no checksum for $url. Run task tools:checksums."
    done < <(comm -23 <(printf '%s\n' "$expected") <(printf '%s\n' "$recorded"))
    while IFS= read -r url; do
        [[ -n "$url" ]] || continue
        report "$sums has a line for $url, which no pin in scripts/lib/versions.sh produces. Run task tools:checksums."
    done < <(comm -13 <(printf '%s\n' "$expected") <(printf '%s\n' "$recorded"))
}

check_node
check_uv
check_setup_uv
check_pytest_pins
check_helm
check_npm_pins
check_openspec_stamps
check_single_installs
check_checksums

if [[ "$failed" -ne 0 ]]; then
    exit 1
fi
echo "All pinned tool versions match scripts/lib/versions.sh (node $NODE_VERSION, uv $UV_VERSION, helm $HELM_VERSION)."
