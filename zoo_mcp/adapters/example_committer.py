from datetime import datetime
from pathlib import Path
from typing import List, Optional
import re
from zoo_mcp.zoo_models import ExampleMetadata, TaskMetadata, ZooMetadata
from zoo_mcp.storage import (
    get_example_path,
    get_task_path,
    get_zoo_path,
    load_json,
    save_json,
    generate_id,
)
from zoo_mcp.analyzer import analyze_file
from zoo_mcp.schemas import GHGetContentsOutput, CodeItem, GrepHit, SOAnswer, IssueWithCode


def _create_example_structure(task_path: Path, description: str, tags: List[str], source_type: str, source_tool: str, source_url: str, repo: Optional[str] = None, ref: Optional[str] = None, language: Optional[str] = None) -> tuple[Path, str]:
    """Create example directory and return path and ID"""
    example_id = generate_id("ex")
    example_path = task_path / "examples" / example_id
    example_path.mkdir(parents=True, exist_ok=True)

    source_files_dir = example_path / "source_files"
    source_files_dir.mkdir(exist_ok=True)

    now = datetime.utcnow().isoformat() + "Z"

    meta = ExampleMetadata(
        id=example_id,
        task_id=task_path.name,
        source_type=source_type,
        source_tool=source_tool,
        source_url=source_url,
        repo=repo,
        ref=ref,
        description=description,
        tags=tags,
        language=language,
        created_at=now,
        updated_at=now,
        files=[],
        stats={}
    )

    return example_path, example_id, meta


def _finalize_example(workspace: Path, zoo_id: str, task_id: str, example_path: Path, meta: ExampleMetadata) -> ExampleMetadata:
    """Save metadata and update counters"""
    total_lines = sum(f.lines for f in meta.files)
    total_bytes = sum(f.size_bytes for f in meta.files)

    meta.stats = {
        "total_lines": total_lines,
        "total_files": len(meta.files),
        "total_bytes": total_bytes,
        "main_concepts": list(set(concept for f in meta.files for concept in f.key_concepts))[:10]
    }

    meta_json_path = example_path / "meta.json"
    save_json(meta_json_path, meta.model_dump())

    task_path = get_task_path(workspace, zoo_id, task_id)
    task_json = task_path / "task.json"
    if task_json.exists():
        task_meta = TaskMetadata(**load_json(task_json))
        task_meta.example_count += 1
        task_meta.updated_at = meta.updated_at
        save_json(task_json, task_meta.model_dump())

    zoo_path = get_zoo_path(workspace, zoo_id)
    zoo_json = zoo_path / "zoo.json"
    if zoo_json.exists():
        zoo_meta = ZooMetadata(**load_json(zoo_json))
        zoo_meta.example_count += 1
        zoo_meta.updated_at = meta.updated_at
        save_json(zoo_json, zoo_meta.model_dump())

    return meta


def commit_from_gh_get_contents(workspace: Path, zoo_id: str, task_id: str, result: dict, description: str, tags: List[str]) -> ExampleMetadata:
    """Commit example from gh_get_contents result"""
    task_path = get_task_path(workspace, zoo_id, task_id)

    items = result.get("items", [])
    if not items:
        raise ValueError("No content items in result")

    first_item = items[0]
    repo = result.get("repo", "unknown")
    source_url = first_item.get("download_url", "")

    example_path, example_id, meta = _create_example_structure(
        task_path=task_path,
        description=description,
        tags=tags,
        source_type="github",
        source_tool="gh_get_contents",
        source_url=source_url,
        repo=repo,
        ref=result.get("ref")
    )

    source_files_dir = example_path / "source_files"

    for item in items:
        if item.get("content"):
            filename = item["name"]
            content = item["content"]

            file_path = source_files_dir / filename
            file_path.write_text(content, encoding='utf-8')

            relative_path = f"source_files/{filename}"
            file_meta = analyze_file(filename, content, relative_path)
            meta.files.append(file_meta)

            if not meta.language and file_meta.language:
                meta.language = file_meta.language

    return _finalize_example(workspace, zoo_id, task_id, example_path, meta)


def commit_from_gh_search_code(workspace: Path, zoo_id: str, task_id: str, github_adapter, code_item: dict, description: str, tags: List[str]) -> ExampleMetadata:
    """Fetch file from code search result and commit"""
    task_path = get_task_path(workspace, zoo_id, task_id)

    repo_parts = code_item["repository"].split("/")
    if len(repo_parts) != 2:
        raise ValueError(f"Invalid repository format: {code_item['repository']}")

    owner, repo = repo_parts
    path = code_item["path"]

    result = github_adapter.get_contents(owner, repo, path)

    if result["type"] != "file":
        raise ValueError("Expected file, got directory")

    example_path, example_id, meta = _create_example_structure(
        task_path=task_path,
        description=description,
        tags=tags,
        source_type="github",
        source_tool="gh_search_code",
        source_url=code_item["html_url"],
        repo=code_item["repository"],
        ref=None
    )

    source_files_dir = example_path / "source_files"

    for item in result["items"]:
        if item.get("content"):
            filename = item["name"]
            content = item["content"]

            file_path = source_files_dir / filename
            file_path.write_text(content, encoding='utf-8')

            relative_path = f"source_files/{filename}"
            file_meta = analyze_file(filename, content, relative_path)
            meta.files.append(file_meta)

            if not meta.language and file_meta.language:
                meta.language = file_meta.language

    return _finalize_example(workspace, zoo_id, task_id, example_path, meta)


def commit_from_grep_search(workspace: Path, zoo_id: str, task_id: str, github_adapter, grep_hit: dict, fetch_full_file: bool, description: str, tags: List[str]) -> ExampleMetadata:
    """Commit from grep search (snippet or full file)"""
    task_path = get_task_path(workspace, zoo_id, task_id)

    repo = grep_hit["repo"]
    ref = grep_hit["ref"]
    path = grep_hit["path"]

    example_path, example_id, meta = _create_example_structure(
        task_path=task_path,
        description=description,
        tags=tags,
        source_type="grep",
        source_tool="grep_search",
        source_url=grep_hit["url"],
        repo=repo,
        ref=ref
    )

    source_files_dir = example_path / "source_files"
    filename = Path(path).name

    if fetch_full_file:
        try:
            repo_parts = repo.split("/")
            if len(repo_parts) == 2:
                owner, repo_name = repo_parts
                result = github_adapter.get_contents(owner, repo_name, path, ref)

                if result["type"] == "file" and result["items"]:
                    content = result["items"][0].get("content", "")
                else:
                    content = grep_hit["snippet"]
            else:
                content = grep_hit["snippet"]
        except Exception:
            content = grep_hit["snippet"]
    else:
        content = grep_hit["snippet"]

    file_path = source_files_dir / filename
    file_path.write_text(content, encoding='utf-8')

    relative_path = f"source_files/{filename}"
    file_meta = analyze_file(filename, content, relative_path)
    meta.files.append(file_meta)
    meta.language = file_meta.language

    return _finalize_example(workspace, zoo_id, task_id, example_path, meta)


def commit_from_so_accepted(workspace: Path, zoo_id: str, task_id: str, so_answer: dict, description: str, tags: List[str]) -> ExampleMetadata:
    """Commit Stack Overflow code blocks"""
    task_path = get_task_path(workspace, zoo_id, task_id)

    example_path, example_id, meta = _create_example_structure(
        task_path=task_path,
        description=description,
        tags=tags,
        source_type="stackoverflow",
        source_tool="so_accepted",
        source_url=so_answer["answer_url"]
    )

    source_files_dir = example_path / "source_files"

    readme_content = f"# {so_answer['question']}\n\nSource: {so_answer['answer_url']}\n\n"
    readme_path = source_files_dir / "README.md"
    readme_path.write_text(readme_content, encoding='utf-8')

    for idx, block in enumerate(so_answer.get("code_blocks", [])):
        lang = block.get("lang") or "txt"
        code_text = block["text"]

        ext_map = {
            "python": "py", "javascript": "js", "typescript": "ts",
            "java": "java", "cpp": "cpp", "c": "c", "rust": "rs",
            "go": "go", "ruby": "rb", "php": "php"
        }
        ext = ext_map.get(lang, lang)

        filename = f"code_{idx+1}.{ext}"
        file_path = source_files_dir / filename
        file_path.write_text(code_text, encoding='utf-8')

        relative_path = f"source_files/{filename}"
        file_meta = analyze_file(filename, code_text, relative_path)
        meta.files.append(file_meta)

        if not meta.language and file_meta.language:
            meta.language = file_meta.language

    return _finalize_example(workspace, zoo_id, task_id, example_path, meta)


def commit_from_gh_issues(workspace: Path, zoo_id: str, task_id: str, issue: dict, description: str, tags: List[str]) -> ExampleMetadata:
    """Commit code from GitHub issue"""
    task_path = get_task_path(workspace, zoo_id, task_id)

    example_path, example_id, meta = _create_example_structure(
        task_path=task_path,
        description=description,
        tags=tags,
        source_type="github_issue",
        source_tool="gh_issues_with_code",
        source_url=issue["html_url"]
    )

    source_files_dir = example_path / "source_files"

    readme_content = f"# Issue #{issue['number']}: {issue['title']}\n\nSource: {issue['html_url']}\n\n"
    readme_path = source_files_dir / "README.md"
    readme_path.write_text(readme_content, encoding='utf-8')

    for idx, block in enumerate(issue.get("code_blocks", [])):
        lang = block.get("lang") or "txt"
        code_text = block["text"]

        ext_map = {
            "python": "py", "javascript": "js", "typescript": "ts",
            "java": "java", "cpp": "cpp", "c": "c", "rust": "rs",
            "go": "go", "ruby": "rb", "php": "php"
        }
        ext = ext_map.get(lang, lang)

        filename = f"code_{idx+1}.{ext}"
        file_path = source_files_dir / filename
        file_path.write_text(code_text, encoding='utf-8')

        relative_path = f"source_files/{filename}"
        file_meta = analyze_file(filename, code_text, relative_path)
        meta.files.append(file_meta)

        if not meta.language and file_meta.language:
            meta.language = file_meta.language

    return _finalize_example(workspace, zoo_id, task_id, example_path, meta)


def commit_from_url(workspace: Path, zoo_id: str, task_id: str, github_adapter, url: str, description: str, tags: List[str]) -> ExampleMetadata:
    """Fetch from URL and commit (GitHub URLs only)"""
    github_pattern = r'github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.+)'
    match = re.match(github_pattern, url)

    if not match:
        raise ValueError("Only GitHub blob URLs are supported")

    owner, repo, ref, path = match.groups()

    result = github_adapter.get_contents(owner, repo, path, ref)

    return commit_from_gh_get_contents(workspace, zoo_id, task_id, result, description, tags)


def commit_from_content(workspace: Path, zoo_id: str, task_id: str, filename: str, content: str, language: Optional[str], description: str, tags: List[str], source_url: Optional[str] = None) -> ExampleMetadata:
    """Commit direct content"""
    task_path = get_task_path(workspace, zoo_id, task_id)

    example_path, example_id, meta = _create_example_structure(
        task_path=task_path,
        description=description,
        tags=tags,
        source_type="direct",
        source_tool="manual",
        source_url=source_url or "direct_input",
        language=language
    )

    source_files_dir = example_path / "source_files"

    file_path = source_files_dir / filename
    file_path.write_text(content, encoding='utf-8')

    relative_path = f"source_files/{filename}"
    file_meta = analyze_file(filename, content, relative_path)
    meta.files.append(file_meta)

    if not meta.language and file_meta.language:
        meta.language = file_meta.language

    return _finalize_example(workspace, zoo_id, task_id, example_path, meta)


def commit_from_exa_search(workspace: Path, zoo_id: str, task_id: str, exa_result: dict, description: str, tags: List[str]) -> ExampleMetadata:
    """Commit from Exa general search result"""
    task_path = get_task_path(workspace, zoo_id, task_id)

    url = exa_result["url"]
    title = exa_result["title"]
    text = exa_result.get("text", "")
    repo = exa_result.get("repo")
    ref = exa_result.get("ref")

    example_path, example_id, meta = _create_example_structure(
        task_path=task_path,
        description=description,
        tags=tags,
        source_type="exa",
        source_tool="exa_search",
        source_url=url,
        repo=repo,
        ref=ref
    )

    source_files_dir = example_path / "source_files"

    readme_content = f"# {title}\n\nSource: {url}\n"
    if exa_result.get("author"):
        readme_content += f"Author: {exa_result['author']}\n"
    if exa_result.get("published_date"):
        readme_content += f"Published: {exa_result['published_date']}\n"
    readme_content += f"\n{text[:5000]}\n"

    readme_path = source_files_dir / "README.md"
    readme_path.write_text(readme_content, encoding='utf-8')

    relative_path = "source_files/README.md"
    file_meta = analyze_file("README.md", readme_content, relative_path)
    meta.files.append(file_meta)

    return _finalize_example(workspace, zoo_id, task_id, example_path, meta)


def commit_from_exa_code_search(workspace: Path, zoo_id: str, task_id: str, github_adapter, exa_result: dict, fetch_full: bool, description: str, tags: List[str]) -> ExampleMetadata:
    """Commit from Exa code search result"""
    task_path = get_task_path(workspace, zoo_id, task_id)

    url = exa_result["url"]
    title = exa_result["title"]
    text = exa_result.get("text", "")
    repo = exa_result.get("repo")
    ref = exa_result.get("ref")
    path = exa_result.get("path")

    example_path, example_id, meta = _create_example_structure(
        task_path=task_path,
        description=description,
        tags=tags,
        source_type="exa",
        source_tool="exa_code_search",
        source_url=url,
        repo=repo,
        ref=ref
    )

    source_files_dir = example_path / "source_files"

    if repo and path and fetch_full and github_adapter:
        try:
            repo_parts = repo.split("/")
            if len(repo_parts) == 2:
                owner, repo_name = repo_parts
                result = github_adapter.get_contents(owner, repo_name, path, ref)

                if result["type"] == "file" and result["items"]:
                    content = result["items"][0].get("content", "")
                    filename = Path(path).name

                    file_path = source_files_dir / filename
                    file_path.write_text(content, encoding='utf-8')

                    relative_path = f"source_files/{filename}"
                    file_meta = analyze_file(filename, content, relative_path)
                    meta.files.append(file_meta)
                    meta.language = file_meta.language
                else:
                    raise ValueError("Not a file")
            else:
                raise ValueError("Invalid repo format")
        except Exception:
            readme_content = f"# {title}\n\nSource: {url}\n\n{text[:5000]}\n"
            readme_path = source_files_dir / "README.md"
            readme_path.write_text(readme_content, encoding='utf-8')

            relative_path = "source_files/README.md"
            file_meta = analyze_file("README.md", readme_content, relative_path)
            meta.files.append(file_meta)
    else:
        readme_content = f"# {title}\n\nSource: {url}\n\n{text[:5000]}\n"
        readme_path = source_files_dir / "README.md"
        readme_path.write_text(readme_content, encoding='utf-8')

        relative_path = "source_files/README.md"
        file_meta = analyze_file("README.md", readme_content, relative_path)
        meta.files.append(file_meta)

    return _finalize_example(workspace, zoo_id, task_id, example_path, meta)


def commit_from_exa_find_similar(workspace: Path, zoo_id: str, task_id: str, exa_result: dict, description: str, tags: List[str]) -> ExampleMetadata:
    """Commit from Exa find_similar result"""
    return commit_from_exa_search(workspace, zoo_id, task_id, exa_result, description, tags)