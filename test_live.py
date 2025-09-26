import os
import sys
from dotenv import load_dotenv

load_dotenv(".env.local")

from zoo_mcp.adapters.github import GitHubAdapter
from zoo_mcp.adapters.grep import GrepAdapter
from zoo_mcp.adapters.librariesio import LibrariesIOAdapter
from zoo_mcp.adapters.stackexchange import StackExchangeAdapter
from pathlib import Path

def test_github():
    token = os.getenv("GITHUB_TOKEN")
    adapter = GitHubAdapter(token=token, workspace=Path("./workspace"))

    print("Testing GitHub adapter...")
    result = adapter.search_repos("fastapi websocket", per_page=3)
    print(f"  [OK] Found {len(result['items'])} repos")
    print(f"  [OK] Rate limit: {result['rate']['remaining']} remaining")
    if result['items']:
        print(f"  [OK] Example: {result['items'][0]['full_name']}")
    return True

def test_grep():
    url = os.getenv("GREP_API_URL", "https://grep.app/api/search")
    adapter = GrepAdapter(api_url=url)

    print("\nTesting Grep adapter...")
    result = adapter.search("use axum", language="Rust", limit=3)
    print(f"  [OK] Found {len(result['hits'])} code hits")
    if result['hits']:
        print(f"  [OK] Example: {result['hits'][0]['repo']}")
    return True

def test_librariesio():
    key = os.getenv("LIBRARIESIO_API_KEY")
    if not key:
        print("\nSkipping Libraries.io (no API key)")
        return True

    adapter = LibrariesIOAdapter(api_key=key)

    print("\nTesting Libraries.io adapter...")
    result = adapter.get_dependents("fastapi", "pypi", limit=3)
    print(f"  [OK] Found {len(result['dependents'])} dependents")
    if result['dependents']:
        print(f"  [OK] Example: {result['dependents'][0]['repo']}")
    return True

def test_stackexchange():
    key = os.getenv("STACKEXCHANGE_KEY")
    adapter = StackExchangeAdapter(api_key=key)

    print("\nTesting Stack Exchange adapter...")
    result = adapter.search_accepted_answers("fastapi websocket", limit=2)
    print(f"  [OK] Found {len(result['answers'])} answers with code")
    if result['answers']:
        print(f"  [OK] Example: {result['answers'][0]['question'][:50]}...")
    return True

if __name__ == "__main__":
    print("=" * 50)
    print("Zoo MCP Live API Test")
    print("=" * 50)

    try:
        test_github()
        test_grep()
        test_librariesio()
        test_stackexchange()
        print("\n" + "=" * 50)
        print("[SUCCESS] All live tests passed!")
        print("=" * 50)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)