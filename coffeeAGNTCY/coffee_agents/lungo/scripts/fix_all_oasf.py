#!/usr/bin/env python3
import json
import os
from pathlib import Path

# Valid domain/skill mappings from OASF taxonomy
DOMAIN_API_INTEGRATION = {"id": 10204, "name": "technology/software_engineering/apis_integration"}
SKILL_AGENT_COORDINATION = {"id": 1004, "name": "agent_orchestration/agent_coordination"}

def fix_oasf_file(file_path):
    """Fix OASF file to match v1.0.0 schema"""
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    # Use valid domain and skill for all agents
    data['domains'] = [DOMAIN_API_INTEGRATION]
    data['skills'] = [SKILL_AGENT_COORDINATION]
    
    # Fix modules
    if 'modules' in data and len(data['modules']) > 0:
        module = data['modules'][0]
        
        # Remove module ID if present (not in sample)
        if 'id' in module:
            del module['id']
        
        # Fix module data
        if 'data' in module:
            # Remove invalid fields
            if 'name' in module['data']:
                del module['data']['name']
            
            # Rename connections to servers
            if 'connections' in module['data']:
                module['data']['servers'] = module['data'].pop('connections')
    
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

print("\nAll files fixed!")
