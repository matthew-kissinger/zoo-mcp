import os
import sys
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(".env.local")

from zoo_mcp.server import (
    gh_search_repos,
    gh_search_code,
    gh_get_contents,
    gh_get_archive,
    gh_releases,
    gh_issues_with_code,
    grep_search,
    libsio_dependents,
    so_accepted,
)

print("=" * 60)
print("Testing all 9 Zoo MCP tools")
print("=" * 60)

print("\n1. Testing gh_search_repos...")
try:
    result = gh_search_repos(q="rust async websocket", per_page=2)
    print(f"   [OK] Found {len(result['items'])} repos")
    if result['items']:
        print(f"   Example: {result['items'][0]['full_name']}")
except Exception as e:
    print(f"   [ERROR] {e}")

print("\n2. Testing gh_search_code...")
try:
    result = gh_search_code(q="fastapi WebSocket language:python", per_page=2)
    print(f"   [OK] Found {len(result['items'])} code files")
    if result['items']:
        print(f"   Example: {result['items'][0]['repository']}/{result['items'][0]['path']}")
except Exception as e:
    print(f"   [ERROR] {e}")

print("\n3. Testing gh_get_contents...")
try:
    result = gh_get_contents(owner="fastapi", repo="fastapi", path="README.md")
    print(f"   [OK] Got {result['type']} with {len(result['items'])} items")
    if result['items']:
        print(f"   Example: {result['items'][0]['name']} ({result['items'][0]['size']} bytes)")
except Exception as e:
    print(f"   [ERROR] {e}")

print("\n4. Testing gh_get_archive...")
try:
    result = gh_get_archive(owner="fastapi", repo="fastapi", ref="master", format="zipball")
    print(f"   [OK] Downloaded {result['bytes']} bytes")
    print(f"   Path: {result['archive_path']}")
except Exception as e:
    print(f"   [ERROR] {e}")

print("\n5. Testing gh_releases...")
try:
    result = gh_releases(owner="fastapi", repo="fastapi", limit=3)
    print(f"   [OK] Found {len(result['releases'])} releases")
    if result['releases']:
        print(f"   Latest: {result['releases'][0]['tag']}")
except Exception as e:
    print(f"   [ERROR] {e}")

print("\n6. Testing gh_issues_with_code...")
try:
    result = gh_issues_with_code(owner="fastapi", repo="fastapi", q="websocket", limit=2)
    print(f"   [OK] Found {len(result['items'])} issues with code")
    if result['items']:
        print(f"   Example: #{result['items'][0]['number']} - {result['items'][0]['title'][:50]}...")
except Exception as e:
    print(f"   [ERROR] {e}")

print("\n7. Testing grep_search...")
try:
    result = grep_search(query="use tokio::net::TcpListener", language="Rust", limit=3)
    print(f"   [OK] Found {len(result['hits'])} code hits")
    if result['hits']:
        print(f"   Example: {result['hits'][0]['repo']} - {result['hits'][0]['path']}")
except Exception as e:
    print(f"   [ERROR] {e}")

print("\n8. Testing libsio_dependents...")
try:
    result = libsio_dependents(package="tokio", ecosystem="cargo", limit=3)
    print(f"   [OK] Found {len(result['dependents'])} dependents")
    if result['dependents']:
        print(f"   Example: {result['dependents'][0]['repo']}")
except Exception as e:
    print(f"   [ERROR] {e}")

print("\n9. Testing so_accepted...")
try:
    result = so_accepted(q="python asyncio websocket", tags=["python"], limit=2)
    print(f"   [OK] Found {len(result['answers'])} answers with code")
    if result['answers']:
        print(f"   Example: {result['answers'][0]['question'][:50]}...")
except Exception as e:
    print(f"   [ERROR] {e}")

print("\n" + "=" * 60)
print("All tool tests completed!")
print("=" * 60)