import json
import logging
from pathlib import Path
from google.protobuf.struct_pb2 import Struct
from google.protobuf.json_format import ParseDict
from agntcy.dir_sdk.models import core_v1
from agent_recruiter.agent_registries.ads.directory import ADS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def publish_example_agents_cards():
    try:
        directory = ADS()
    except ImportError:
        logger.error("agent-recruiter package is required to publish cards.")
        return

    # for each example agent, publish its card to the directory
    folders_in_cwd = [f.name for f in Path(__file__).parent.iterdir() if f.is_dir()]

    for agent in folders_in_cwd:
        card_path = Path(__file__).parent / agent / "oasf_record.json"
        if not card_path.exists():
            logger.warning(f"No card found for agent: {agent}")
            continue

        publish_card(card_path, directory)

def publish_card(card_path: Path, directory: ADS):
    with open(card_path, "r") as f:
        card_data = json.load(f)

    # Add schema_version if missing (required by Directory)
    if "schema_version" not in card_data:
        card_data["schema_version"] = "1.0.0"

    # Create Record
    # The Record.data field is a Struct
    data_struct = Struct()
    ParseDict(card_data, data_struct)

    record = core_v1.Record(
        data=data_struct
    )

    logger.info(f"Pushing record for {card_path.stem}...")
    directory.push_agent_record(record)

if __name__ == "__main__":
    publish_example_agents_cards()