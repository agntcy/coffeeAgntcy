from typing import Optional, Any
import grpc
import json
from google.protobuf.struct_pb2 import Struct
from google.protobuf.json_format import MessageToJson
from agntcy.dir_sdk.models import core_v1

from agntcy.oasfsdk.validation.v1.validation_service_pb2 import ValidateRecordRequest
from agntcy.oasfsdk.validation.v1.validation_service_pb2_grpc import (
    ValidationServiceStub,
)
from agntcy.oasfsdk.translation.v1.translation_service_pb2 import (
    A2AToRecordRequest,
    RecordToA2ARequest,
)
from agntcy.oasfsdk.translation.v1.translation_service_pb2_grpc import (
    TranslationServiceStub,
)

from a2a.types import (
    AgentCard,
)


class SemanticTranslator:
    """
    Handles translation and validation between agent semantic protocols such as
    A2A, MCP, and OASF record formats.

    Translation and validation is performed by the oasf-sdk gRPC service.
    """

    def __init__(
        self, host: str = "localhost", port: int = 31234, auto_connect: bool = True
    ):
        """
        Initialize the SemanticTranslator.

        Args:
            host: gRPC server host
            port: gRPC server port
            auto_connect: If True, establishes connection immediately.
                         If False, call connect() manually.
        """
        self.address = f"{host}:{port}"
        self._channel: Optional[grpc.Channel] = None
        self._translation_stub: Optional[TranslationServiceStub] = None
        self._validation_stub: Optional[ValidationServiceStub] = None
        self._managed_context = False
        self.to_translators = {
            "A2A": self.oasf_to_a2a,
        }
        self.from_translators = {
            "A2A": self.a2a_to_oasf,
        }

        if auto_connect:
            self.connect()

    def translate_to(self, protocol: str, record: dict) -> Any:
        """
        Translate an OASF record to the specified protocol format.

        Args:
            protocol: Target protocol (e.g., "A2A")
            record: Dictionary containing the OASF record

        Returns:
            Protobuf Struct representation of the translated record
        """
        translator = self.to_translators.get(protocol)
        if not translator:
            raise ValueError(f"Unsupported protocol: {protocol}")
        return translator(record)

    def translate_from(self, protocol: str, record: dict) -> Any:
        """
        Translate a record from the specified protocol format to OASF.

        Args:
            protocol: Source protocol (e.g., "A2A")
            record: Dictionary containing the record in the source protocol format
        Returns:
            String representation of the translated OASF record
        """
        translator = self.from_translators.get(protocol)
        if not translator:
            raise ValueError(f"Unsupported protocol: {protocol}")
        return translator(record)

    def connect(self) -> None:
        """Establish gRPC connection and initialize stubs."""
        if self._channel is None:
            self._channel = grpc.insecure_channel(self.address)
            self._translation_stub = TranslationServiceStub(self._channel)
            self._validation_stub = ValidationServiceStub(self._channel)

    def close(self) -> None:
        """Close gRPC connection and cleanup resources."""
        if self._channel:
            self._channel.close()
            self._channel = None
            self._translation_stub = None
            self._validation_stub = None

    def __enter__(self):
        """Context manager entry - establishes gRPC connection."""
        self._managed_context = True
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - closes gRPC connection."""
        if self._managed_context:
            self.close()
            self._managed_context = False

    def __del__(self):
        """Cleanup on garbage collection."""
        self.close()

    def _oasf_sdk_record_to_dir_sdk_record(
        self, record_struct: Struct
    ) -> core_v1.Record:
        """
        Convert OASF record Struct to core_v1.Record.

        Args:
            record_struct: Protobuf Struct representation of the OASF record

        Returns:
            core_v1.Record instance
        """
        record_dict = json.loads(MessageToJson(record_struct))

        record = core_v1.Record()
        record.data.update(record_dict)

        return record

    def _dir_sdk_record_to_oasf_sdk_record(self, record: core_v1.Record) -> Struct:
        """
        Convert core_v1.Record to OASF record Struct.

        Args:
            record: core_v1.Record instance

        Returns:
            Protobuf Struct representation of the OASF record
        """
        record_dict = json.loads(MessageToJson(record.data))
        record_struct = Struct()
        record_struct.update(record_dict)

        return record_struct

    def validate_oasf(self, record_data: dict) -> tuple[bool, list[str]]:
        """
        Validate an OASF record.

        Args:
            record_data: Dictionary containing the OASF record to validate

        Returns:
            Tuple of (is_valid, errors) where errors is a list of error messages

        Raises:
            RuntimeError: If not connected
            grpc.RpcError: If the gRPC call fails
        """
        if not self._validation_stub:
            raise RuntimeError(
                "Not connected. Call connect() or use as context manager."
            )

        record_struct = Struct()
        record_struct.update(record_data)

        request = ValidateRecordRequest(record=record_struct)
        response = self._validation_stub.ValidateRecord(request)

        return response.is_valid, list(response.errors)

    def a2a_to_oasf(self, agent_card: AgentCard) -> core_v1.Record:
        """
        Translate an A2A AgentCard to an OASF record.

        Args:
            agent_card: The A2A AgentCard to translate

        Returns:
            Protobuf Struct containing the OASF record, or None if translation fails

        Raises:
            RuntimeError: If not connected
            grpc.RpcError: If the gRPC call fails
        """
        if not self._translation_stub:
            raise RuntimeError(
                "Not connected. Call connect() or use as context manager."
            )

        dict_agent_card = json.loads(agent_card.model_dump_json())
        data = {"a2aCard": dict_agent_card}

        record_struct = Struct()
        record_struct.update(data)

        request = A2AToRecordRequest(data=record_struct)
        response = self._translation_stub.A2AToRecord(request)

        # write to file for debugging
        with open("oasf_record_from_a2a.json", "w") as f:
            f.write(MessageToJson(response.record))

        # need to return a core_v1.Record
        return self._oasf_sdk_record_to_dir_sdk_record(response.record)

    def oasf_to_a2a(self, record: core_v1.Record) -> AgentCard:
        """
        Translate an OASF record to an A2A Card.

        Args:
            record: core_v1.Record containing the OASF record

        Returns:
            String containing the A2A Card

        Raises:
            RuntimeError: If not connected
            grpc.RpcError: If the gRPC call fails
        """
        if not self._translation_stub:
            raise RuntimeError(
                "Not connected. Call connect() or use as context manager."
            )

        record_struct = self._dir_sdk_record_to_oasf_sdk_record(record)

        request = RecordToA2ARequest(record=record_struct)
        response = self._translation_stub.RecordToA2A(request)

        data_dict = json.loads(MessageToJson(response.data))
        card_data = data_dict.get("a2aCard", {})

        return AgentCard.model_validate(card_data)
    
if __name__ == "__main__":
    from a2a.types import (
        AgentCapabilities,
        AgentCard,
        AgentSkill,
    )
    skill = AgentSkill(
        id="hello_world",
        name="Returns hello world",
        description="just returns hello world",
        tags=["hello world"],
        examples=["hi", "hello world"],
    )
    # --8<-- [end:AgentSkill]

    extended_skill = AgentSkill(
        id="super_hello_world",
        name="Returns a SUPER Hello World",
        description="A more enthusiastic greeting, only for authenticated users.",
        tags=["hello world", "super", "extended"],
        examples=["super hi", "give me a super hello"],
    )

    # --8<-- [start:AgentCard]
    # This will be the public-facing agent card
    public_agent_card = AgentCard(
        name="Hello World Agent",
        description="Just a hello world agent",
        url="http://0.0.0.0:9999/",
        version="1.0.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[skill],  # Only the basic skill for the public card
        supports_authenticated_extended_card=True,
    )

    translator = SemanticTranslator()
    with translator:
        # Translate A2A to OASF
        oasf_record = translator.a2a_to_oasf(public_agent_card)
        print("Translated OASF Record from A2A:")
        print(oasf_record)