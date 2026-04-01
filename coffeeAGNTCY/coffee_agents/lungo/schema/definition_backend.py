# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Protocol for schema definition backends (dispatch target for ``schema.validation``)."""

from pathlib import Path
from typing import Protocol, runtime_checkable

from schema import errors


@runtime_checkable
class DefinitionBackend(Protocol):
    def owns_schema(self, schema_name: str) -> bool: ...

    def validate_definition(self, schema_name: str) -> Path: ...

    def validate_all_definitions(self) -> list[errors.SchemaDefinitionError]: ...

    def validate_data(self, data: dict, schema_name: str) -> None: ...

    def parse_instance_file(self, path: Path) -> dict: ...

    def parse_instance_text(self, text: str) -> dict: ...

    def get_schema(self, schema_name: str) -> dict: ...
