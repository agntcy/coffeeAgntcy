"""Version and dependency utilities for Lungo exchange service.

Includes helpers to extract dependency versions and to derive a local
git-based fallback for build version and date when running outside CI.
"""

import configparser
import logging
import re
from pathlib import Path
import subprocess
from typing import Optional, Tuple

try:
    import tomllib  # Python 3.11+
except Exception:  # pragma: no cover
    tomllib = None

logger = logging.getLogger(__name__)


DISPLAY_NAMES = {
    "agntcy-app-sdk": "AGNTCY App SDK",
    "a2a-sdk": "A2A",
    "ioa-observe-sdk": "Observe SDK",
    "langgraph": "LangGraph",
    "identity-service-sdk": "Identity",
    "mcp": "MCP",
}


def _extract_name_and_version(spec: str):
    """Extract base package name and version constraint from a dependency spec.

    Handles extras (e.g., mcp[cli]>=1.10.0) and environment markers (e.g., ; python_version>='3.11').

    Returns tuple (base_name, op, version) where op is one of '==', '>=', or '' if unspecified.
    """
   
    s = spec.split(';', 1)[0].strip()
    s = re.sub(r"\s*(==|>=)\s*", r" \1 ", s)
    name_part = s.split('[', 1)[0]
    m = re.search(r"\s(==|>=)\s([^\s]+)", s)
    if m:
        op, ver = m.group(1), m.group(2)
        name = name_part.split(op)[0].strip()
        return name.strip(), op, ver.strip()

    return name_part.strip(), "", ""


def get_dependencies():
    """Get dependency versions from pyproject.toml and docker-compose.yaml"""
    try:
        dependencies: dict[str, str] = {}

        # Parse pyproject.toml for Python dependencies
        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        if pyproject_path.exists() and tomllib is not None:
            with open(pyproject_path, 'rb') as f:
                data = tomllib.load(f)

            for dep in data.get('project', {}).get('dependencies', []):
                name, op, ver = _extract_name_and_version(dep)
                display = DISPLAY_NAMES.get(name)
                if not display:
                    continue
                if op == '==':
                    dependencies[display] = f"v{ver}"
                elif op == '>=':
                    dependencies[display] = f">= v{ver}"
                else:
                    dependencies[display] = "unknown"

        # Get SLIM version from docker-compose.yaml
        compose_path = Path(__file__).parent.parent / "docker-compose.yaml"
        if compose_path.exists():
            with open(compose_path, 'r') as f:
                content = f.read()
                match = re.search(r'ghcr\.io/agntcy/slim:(\d+\.\d+\.\d+)', content)
                if match:
                    dependencies['SLIM'] = f"v{match.group(1)}"

        return dependencies

    except Exception as e:  
        logger.error(f"Error parsing dependencies: {e}")
        return {}


def _find_git_root(start: Path) -> Optional[Path]:
    """Ascend from 'start' to find a directory that contains a .git folder.

    Returns the git root path if found, else None.
    """
    try:
        p = start.resolve()
        for ancestor in [p, *p.parents]:
            if (ancestor / ".git").exists():
                return ancestor
    except Exception:  
        return None
    return None


def get_latest_tag_and_date(start: Optional[Path] = None) -> Optional[dict]:
    """Return newest tag and its dates from local git.
    """
    try:
        start = start or Path(__file__).parent
        git_root = _find_git_root(start)
        if not git_root:
            return None

        def _run(args: list[str]) -> str:
            return subprocess.check_output(args, cwd=git_root, text=True, stderr=subprocess.DEVNULL).strip()

        out = _run([
            "git", "for-each-ref",
            "--sort=-creatordate",
            "--format=%(refname:short)\t%(creatordate:iso8601)\t%(creatordate:unix)",
            "refs/tags",
        ])
        line = out.splitlines()[0] if out else ""
        if not line:
            return None
        parts = line.split("\t")
        if len(parts) < 3:
            return None
        return {"tag": parts[0], "created_iso": parts[1], "created_unix": parts[2]}
    except Exception as e:  
        logger.debug(f"git fallback failed: {e}")
        return None


def get_version_info(properties_file_path: Path, app_name: str = "lungo-exchange", service_name: str = "lungo-exchange") -> dict:
    """Get complete version information for the application.
    
    Args:
        properties_file_path: Path to the about.properties file
        app_name: Default app name to use as fallback
        service_name: Default service name to use as fallback
        
    Returns:
        Dictionary containing app, service, version, build_date, build_timestamp, image, and dependencies
    """
    try:
        # Try to read from about.properties first
        if properties_file_path.exists():
            config = configparser.ConfigParser()
            with open(properties_file_path, "r") as f:
                config_string = "[DEFAULT]\n" + f.read()
            config.read_string(config_string)
            
            props = dict(config["DEFAULT"])

            app_name_final = props.get("app.name", app_name)
            service_final = props.get("app.service", service_name)
            version = props.get("build.version", props.get("version", "unknown"))
            build_date = props.get("build.date", props.get("date", "unknown"))
            build_ts = props.get("build.timestamp", props.get("timestamp", "unknown"))
            image_name = props.get("image.name", "unknown")
            image_tag = props.get("image.tag", "unknown")
            image = (
                f"{image_name}:{image_tag}" if image_name != "unknown" and image_tag != "unknown" else image_name
            )

            # Fill in any missing values with git fallback
            if version == "unknown" or build_date == "unknown" or build_ts == "unknown":
                git_info = get_latest_tag_and_date(properties_file_path)
                if git_info:
                    if version == "unknown":
                        version = git_info.get("tag", version)
                    if build_date == "unknown":
                        build_date = git_info.get("created_iso", build_date)
                    if build_ts == "unknown":
                        build_ts = git_info.get("created_unix", build_ts)

            return {
                "app": app_name_final,
                "service": service_final,
                "version": version,
                "build_date": build_date,
                "build_timestamp": build_ts,
                "image": image,
                "dependencies": get_dependencies(),
            }

        # No about.properties file found - use git fallback
        logger.error("No about.properties file found - metadata unavailable")
        git_info = get_latest_tag_and_date(properties_file_path)
        if git_info:
            return {
                "app": app_name,
                "service": service_name,
                "version": git_info.get("tag", "unknown"),
                "build_date": git_info.get("created_iso", "unknown"),
                "build_timestamp": git_info.get("created_unix", "unknown"),
                "image": "unknown",
                "dependencies": get_dependencies(),
            }

        # Final fallback - no properties file and no git info
        return {
            "app": app_name,
            "service": service_name,
            "version": "unknown",
            "build_date": "unknown",
            "build_timestamp": "unknown",
            "image": "unknown",
            "dependencies": get_dependencies(),
        }

    except Exception as e:
        logger.error(f"Error getting version info: {e}")
        return {
            "app": app_name,
            "service": service_name,
            "version": "unknown",
            "build_date": "unknown",
            "build_timestamp": "unknown",
            "image": "unknown",
            "dependencies": {},
        }
