#!/usr/bin/env python3
"""Fix OASF records to match dir-api-server v1.0.0 schema"""

import json
from pathlib import Path

# Standard taxonomy mapping
SKILL_MAP = {
    "agent_orchestration/agent_coordination": (1, "agent_orchestration/agent_coordination"),
    "finance/payments/create": (101, "finance/payment_processing"),
    "finance/payments/transactions/list": (101, "finance/payment_processing"),
    "forecasting": (201, "data_analysis/forecasting"),
    "agriculture/coffee_farming": (301, "agriculture/coffee_farming"),
    "logistics/shipping": (401, "logistics/shipping"),
    "finance/accounting": (501, "finance/accounting"),
}

DOMAIN_MAP = {
    "agent_orchestration": (1, "agent_orchestration"),
    "finance/payments": (2, "finance"),
    "payments": (2, "finance"),
    "meteorology": (3, "data_analysis"),
    "agriculture": (4, "agriculture"),
    "logistics": (5, "logistics"),
    "finance": (2, "finance"),
}

def fix_oasf_file(file_path):
    """Fix a single OASF file"""
    with open(file_path) as f:
        data = json.load(f)
    
    # Fix domains
    if "domains" in data:
        fixed_domains = []
        for domain in data["domains"]:
            domain_name = domain.get("name", "")
            if domain_name in DOMAIN_MAP:
                domain_id, standard_name = DOMAIN_MAP[domain_name]
                fixed_domains.append({"id": domain_id, "name": standard_name})
            else:
                # Keep as is but use ID 99 for unknown
                fixed_domains.append({"id": 99, "name": domain_name})
        data["domains"] = fixed_domains
    
    # Fix skills
    if "skills" in data:
        fixed_skills = []
        seen_ids = set()
        for skill in data["skills"]:
            skill_name = skill.get("name", "")
            if skill_name in SKILL_MAP:
                skill_id, standard_name = SKILL_MAP[skill_name]
                if skill_id not in seen_ids:
                    fixed_skills.append({"id": skill_id, "name": standard_name})
                    seen_ids.add(skill_id)
            else:
                # Keep as is
                fixed_skills.append(skill)
        data["skills"] = fixed_skills
    
    # Fix modules - convert connections to servers
    if "modules" in data:
        for i, module in enumerate(data["modules"]):
            # Add module ID if missing
            if "id" not in module:
                module["id"] = f"module-{i}"
            
            # Fix MCP module data
            if module.get("name") == "integration/mcp" and "data" in module:
                module_data = module["data"]
                
                # Convert connections to servers
                if "connections" in module_data:
                    module_data["servers"] = []
                    for conn in module_data["connections"]:
                        server = {
                            "type": conn.get("type", "stdio"),
                            "command": conn.get("command", ""),
                            "args": conn.get("args", [])
                        }
                        module_data["servers"].append(server)
                    del module_data["connections"]
                
                # Remove name field (not in v1.0.0 schema)
                if "name" in module_data:
                    del module_data["name"]
    
    # Write back
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    return True

def main():
    base_dir = Path(__file__).parent.parent
    oasf_dirs = [
        base_dir / "agents/supervisors/auction/oasf/agents",
        base_dir / "agents/supervisors/logistics/oasf/agents",
    ]
    
    fixed = 0
    failed = 0
    
    for oasf_dir in oasf_dirs:
        if not oasf_dir.exists():
            continue
        
        for json_file in oasf_dir.glob("*.json"):
            try:
                fix_oasf_file(json_file)
                print(f"✓ Fixed {json_file.name}")
                fixed += 1
            except Exception as e:
                print(f"✗ Failed {json_file.name}: {e}")
                failed += 1
    
    print(f"\nSummary: {fixed} fixed, {failed} failed")

if __name__ == "__main__":
    main()
