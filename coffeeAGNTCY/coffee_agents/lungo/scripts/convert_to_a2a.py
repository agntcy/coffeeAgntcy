#!/usr/bin/env python3
import json
from pathlib import Path

# Valid domain/skill from taxonomy
DOMAIN_API_INTEGRATION = {"id": 10204, "name": "technology/software_engineering/apis_integration"}
SKILL_AGENT_COORDINATION = {"id": 1004, "name": "agent_orchestration/agent_coordination"}

def fix_oasf_file(file_path):
    """Convert OASF file to use A2A module like the working sample"""
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    # Use valid domain and skill
    data['domains'] = [DOMAIN_API_INTEGRATION]
    data['skills'] = [SKILL_AGENT_COORDINATION]
    
    # Replace MCP module with A2A module (like sample_agent_record.json)
    agent_name = data.get('name', 'Agent')
    agent_desc = data.get('description', 'An AI agent')
    
    data['modules'] = [{
        "name": "integration/a2a",
        "data": {
            "input_modes": ["text/plain", "application/json"],
            "output_modes": ["text/html", "application/json"],
            "protocol_version": "0.3.0",
            "transports": ["http"],
            "capabilities": ["streaming"],
            "security_schemes": ["none"],
            "card_data": {
                "name": agent_name,
                "description": agent_desc,
                "version": "1.0.0",
                "protocolVersion": "0.3.0",
                "defaultInputModes": ["text"],
                "defaultOutputModes": ["text"],
                "preferredTransport": "JSONRPC",
                "capabilities": {"streaming": True},
                "skills": []
            }
        }
    }]
    
    # Write back
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    return file_path.name

# Find all OASF files
base_dir = Path('/home/ubuntu/work/coffeeAgntcy/coffeeAGNTCY/coffee_agents/lungo')
oasf_files = list(base_dir.glob('agents/**/oasf/agents/*.json'))

print(f"Found {len(oasf_files)} OASF files")

for file_path in oasf_files:
    try:
        name = fix_oasf_file(file_path)
        print(f"✓ Fixed {name}")
    except Exception as e:
        print(f"✗ Failed {file_path.name}: {e}")

print("\nAll files converted to A2A module!")
