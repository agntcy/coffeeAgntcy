# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""CLI entry for schema.validation (meta-validate definitions, validate instance data against schemas)."""

import argparse
import pprint
import sys
from pathlib import Path

from schema import errors, validation


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate packaged schema definitions and data instance files.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_all = sub.add_parser(
        "all-definitions",
        help="Validate every packaged schema definition.",
    )
    p_all.set_defaults(handler=_cmd_validate_all_definitions)

    p_one = sub.add_parser(
        "definition",
        help="Validate one packaged schema definition by logical name.",
    )
    p_one.add_argument("schema_name", help="Logical schema name (e.g. session_state_progress_v1).")
    p_one.set_defaults(handler=_cmd_validate_definition)

    p_inst = sub.add_parser(
        "instances",
        help="Validate data instance files against a named schema (backend parses file format, if valid).",
    )
    p_inst.add_argument("schema_name", help="Logical schema name.")
    p_inst.add_argument(
        "files",
        nargs="+",
        type=Path,
        metavar="FILE",
        help="One or more data files.",
    )
    p_inst.set_defaults(handler=_cmd_validate_instance_files)

    p_str = sub.add_parser(
        "instance-string",
        help="Validate one inline instance payload string (e.g. JSON in shell quotes).",
    )
    p_str.add_argument("schema_name", help="Logical schema name.")
    p_str.add_argument(
        "payload",
        help="Payload text as defined by the backend (e.g.: JSON for JSON schemas).",
    )
    p_str.set_defaults(handler=_cmd_validate_instance_string)

    p_get = sub.add_parser(
        "get-schema",
        help="Print the packaged schema definition.",
    )
    p_get.add_argument("schema_name", help="Logical schema name (e.g. session_state_progress_v1).")
    p_get.set_defaults(handler=_cmd_get_schema)

    ns = parser.parse_args(argv)
    return int(ns.handler(ns))


def _cmd_validate_all_definitions(_ns: argparse.Namespace) -> int:
    failures = validation.validate_all_definitions()
    if failures:
        for err in failures:
            loc = f"{err.path}: " if err.path else ""
            print(f"{loc}{err}", file=sys.stderr)
        return 1
    print("All packaged definitions are valid Schemas.")
    return 0


def _cmd_validate_definition(ns: argparse.Namespace) -> int:
    try:
        path = validation.validate_definition(ns.schema_name)
    except errors.SchemaNotFoundError as e:
        print(e, file=sys.stderr)
        return 1
    except errors.AmbiguousSchemaNameError as e:
        print(e, file=sys.stderr)
        return 1
    except errors.SchemaDefinitionError as e:
        loc = f"{e.path}: " if e.path else ""
        print(f"{loc}{e}", file=sys.stderr)
        return 1
    print(f"{path}: ok")
    return 0


def _cmd_validate_instance_files(ns: argparse.Namespace) -> int:
    exit_code = 0
    for path in ns.files:
        if not path.is_file():
            print(f"{path}: not a file", file=sys.stderr)
            exit_code = 1
            continue
        try:
            validation.validate_datafile_against_schema(path, ns.schema_name)
        except errors.InstanceDecodeError as e:
            print(f"{path}: invalid instance file: {e}", file=sys.stderr)
            exit_code = 1
        except errors.SchemaNotFoundError as e:
            print(f"{path}: {e}", file=sys.stderr)
            exit_code = 1
        except errors.AmbiguousSchemaNameError as e:
            print(f"{path}: {e}", file=sys.stderr)
            exit_code = 1
        except errors.SchemaValidationError as e:
            print(f"{path}: {e}", file=sys.stderr)
            exit_code = 1
        except errors.SchemaDefinitionError as e:
            loc = f"{e.path}: " if e.path else ""
            print(f"{path}: schema definition error: {loc}{e}", file=sys.stderr)
            exit_code = 1
        except OSError as e:
            print(f"{path}: {e}", file=sys.stderr)
            exit_code = 1
        else:
            print(f"{path}: ok")
    return exit_code


def _cmd_validate_instance_string(ns: argparse.Namespace) -> int:
    try:
        validation.validate_data_string_against_schema(ns.payload, ns.schema_name)
    except errors.InstanceDecodeError as e:
        print(f"invalid instance payload: {e}", file=sys.stderr)
        return 1
    except errors.SchemaNotFoundError as e:
        print(e, file=sys.stderr)
        return 1
    except errors.AmbiguousSchemaNameError as e:
        print(e, file=sys.stderr)
        return 1
    except errors.SchemaValidationError as e:
        print(e, file=sys.stderr)
        return 1
    except errors.SchemaDefinitionError as e:
        loc = f"{e.path}: " if e.path else ""
        print(f"schema definition error: {loc}{e}", file=sys.stderr)
        return 1
    print("ok")
    return 0


def _cmd_get_schema(ns: argparse.Namespace) -> int:
    try:
        doc = validation.get_schema(ns.schema_name)
    except errors.SchemaNotFoundError as e:
        print(e, file=sys.stderr)
        return 1
    except errors.AmbiguousSchemaNameError as e:
        print(e, file=sys.stderr)
        return 1
    except errors.SchemaDefinitionError as e:
        loc = f"{e.path}: " if e.path else ""
        print(f"{loc}{e}", file=sys.stderr)
        return 1
    pprint.pprint(doc, stream=sys.stdout, width=100)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
