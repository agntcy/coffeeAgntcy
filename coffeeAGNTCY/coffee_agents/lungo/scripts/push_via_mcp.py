#!/usr/bin/env python3
"""Push OASF records to directory via MCP server."""

import json
import subprocess
from pathlib import Path

def push_via_mcp(json_file):
    """Push a record via directory-mcp-server."""
    with open(json_file) as f:
        record = json.load(f)
    
    # Escape the JSON for shell
    record_json = json.dumps(record).replace("'", "'\\''")
    
    # Use docker exec to call the MCP server's push function
    cmd = f"""python3 -c '
import json
import asyncio
import sys
sys.path.insert(0, "/app")
from server import DirectoryMCPServer

async def push():
    server = DirectoryMCPServer()
    record = json.loads('"'"'{record_json}'"'"')
    result = await server.push(record=record)
    print("RESULT:", json.dumps(result))

asyncio.run(push())
'"""
    
    result = subprocess.run(
        ["docker", "exec", "directory-mcp-server", "sh", "-c", cmd],
        capture_output=True,
        text=True
    )
    
    return result.returncode, result.stdout, result.stderr

def main():
    # Find all OASF records
    base = Path("/home/ubuntu/work/coffeeAgntcy/coffeeAGNTCY/coffee_agents/lungo")
    oasf_files = list(base.glob("agents/**/oasf/agents/*.json"))
    
    pushed = 0
    failed = 0
    
    for json_file in oasf_files:
        print(f"Pushing {json_file.name}...", end=" ")
        try:
            exit_code, stdout, stderr = push_via_mcp(json_file)
            
            if exit_code == 0:
                # Parse the result - look for RESULT: prefix
                for line in stdout.strip().split('\n'):
                    if line.startswith('RESULT:'):
                        result = json.loads(line.replace('RESULT:', '').strip())
                        cid = result.get('cid', 'unknown')[:20]
                        print(f"✓ CID: {cid}...")
                        pushed += 1
                        break
                else:
                    print(f"✓ Pushed")
                    pushed += 1
            else:
                error = (stderr or stdout).replace('\n', ' ')[:100]
                print(f"✗ {error}")
                failed += 1
                
        except Exception as e:
            print(f"✗ Error: {e}")
            failed += 1
    
    print(f"\nSummary: {pushed} pushed, {failed} failed")

if __name__ == "__main__":
    main()
