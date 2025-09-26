import json
import subprocess
import sys

def send_mcp_request(request):
    """Send a JSON-RPC request to the MCP server via stdio"""
    proc = subprocess.Popen(
        ["uv", "run", "python", "-m", "zoo_mcp.server", "stdio"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd="C:/Users/Mattm/X/zoo-mcp",
        env=dict(os.environ)
    )

    # Send initialize request first
    init_request = {"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test-client", "version": "1.0"}}}
    proc.stdin.write(json.dumps(init_request) + "\n")
    proc.stdin.flush()

    # Read initialize response
    response_line = proc.stdout.readline()

    # Send actual request
    proc.stdin.write(json.dumps(request) + "\n")
    proc.stdin.flush()

    # Read response
    response_line = proc.stdout.readline()
    proc.terminate()

    if response_line:
        return json.loads(response_line)
    return None

import os

print("=" * 60)
print("Testing Zoo MCP Tools via MCP Protocol")
print("=" * 60)

# Test 1: List tools
print("\n1. Listing available tools...")
request = {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
response = send_mcp_request(request)
if response:
    print(f"   [OK] Found {len(response.get('result', {}).get('tools', []))} tools")
    for tool in response.get('result', {}).get('tools', []):
        print(f"   - {tool['name']}")
else:
    print("   [ERROR] No response")

# Test 2: gh_search_repos
print("\n2. Testing gh_search_repos...")
request = {
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
        "name": "gh_search_repos",
        "arguments": {"q": "rust websocket", "per_page": 2}
    }
}
response = send_mcp_request(request)
if response and 'result' in response:
    result = json.loads(response['result']['content'][0]['text'])
    print(f"   [OK] Found {len(result['items'])} repos")
    if result['items']:
        print(f"   Example: {result['items'][0]['full_name']}")
else:
    print(f"   [ERROR] {response.get('error', 'Unknown error')}")

print("\nTest complete!")