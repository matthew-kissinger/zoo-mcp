from datetime import datetime
from pathlib import Path
from typing import List, Optional
from zoo_mcp.zoo_models import ExampleMetadata, TaskMetadata, ZooMetadata
from zoo_mcp.storage import (
    get_example_path,
    get_task_path,
    get_zoo_path,
    load_json,
    save_json,
    list_subdirs,
    delete_directory,
)
from zoo_mcp.analyzer import analyze_file
from zoo_mcp.adapters import example_committer


def example_commit_from_url(workspace: Path, github_adapter, zoo_id: str, task_id: str, url: str, description: str, tags: Optional[List[str]] = None) -> ExampleMetadata:
    """Commit example from GitHub URL"""
    return example_committer.commit_from_url(
        workspace, zoo_id, task_id, github_adapter, url, description, tags or []
    )


def example_commit_from_content(workspace: Path, zoo_id: str, task_id: str, filename: str, content: str, language: Optional[str], description: str, tags: Optional[List[str]] = None, source_url: Optional[str] = None) -> ExampleMetadata:
    """Commit example from direct content"""
    return example_committer.commit_from_content(
        workspace, zoo_id, task_id, filename, content, language, description, tags or [], source_url
    )


def example_commit_from_search_result(workspace: Path, github_adapter, zoo_id: str, task_id: str, search_type: str, result_data: dict, description: str, tags: Optional[List[str]] = None, fetch_full: bool = True) -> ExampleMetadata:
    """Commit from any search tool result"""
    tags = tags or []

    if search_type == "gh_get_contents":
        return example_committer.commit_from_gh_get_contents(
            workspace, zoo_id, task_id, result_data, description, tags
        )
    elif search_type == "gh_search_code":
        return example_committer.commit_from_gh_search_code(
            workspace, zoo_id, task_id, github_adapter, result_data, description, tags
        )
    elif search_type == "grep_search":
        return example_committer.commit_from_grep_search(
            workspace, zoo_id, task_id, github_adapter, result_data, fetch_full, description, tags
        )
    elif search_type == "stackoverflow":
        return example_committer.commit_from_so_accepted(
            workspace, zoo_id, task_id, result_data, description, tags
        )
    elif search_type == "gh_issues":
        return example_committer.commit_from_gh_issues(
            workspace, zoo_id, task_id, result_data, description, tags
        )
    elif search_type == "exa_search":
        return example_committer.commit_from_exa_search(
            workspace, zoo_id, task_id, result_data, description, tags
        )
    elif search_type == "exa_code_search":
        return example_committer.commit_from_exa_code_search(
            workspace, zoo_id, task_id, github_adapter, result_data, fetch_full, description, tags
        )
    elif search_type == "exa_find_similar":
        return example_committer.commit_from_exa_find_similar(
            workspace, zoo_id, task_id, result_data, description, tags
        )
    else:
        raise ValueError(f"Unsupported search type: {search_type}")


def example_list(workspace: Path, zoo_id: str, task_id: str, language_filter: Optional[str] = None, tag_filter: Optional[List[str]] = None) -> List[dict]:
    """List examples with metadata only (no content)"""
    task_path = get_task_path(workspace, zoo_id, task_id)
    examples_dir = task_path / "examples"

    if not examples_dir.exists():
        return []

    examples = []
    for example_dir in list_subdirs(examples_dir):
        meta_json = example_dir / "meta.json"
        if meta_json.exists():
            try:
                data = load_json(meta_json)

                if language_filter and data.get("language") != language_filter:
                    continue

                if tag_filter:
                    example_tags = set(data.get("tags", []))
                    if not any(tag in example_tags for tag in tag_filter):
                        continue

                summary = {
                    "id": data["id"],
                    "description": data["description"],
                    "tags": data["tags"],
                    "language": data.get("language"),
                    "source_type": data["source_type"],
                    "source_url": data["source_url"],
                    "file_count": len(data.get("files", [])),
                    "total_lines": data.get("stats", {}).get("total_lines", 0),
                    "created_at": data["created_at"]
                }
                examples.append(summary)
            except Exception:
                pass

    return sorted(examples, key=lambda e: e["created_at"], reverse=True)


def example_get_meta(workspace: Path, zoo_id: str, task_id: str, example_id: str) -> ExampleMetadata:
    """Get example metadata only"""
    example_path = get_example_path(workspace, zoo_id, task_id, example_id)
    meta_json = example_path / "meta.json"

    if not meta_json.exists():
        raise FileNotFoundError(f"Example not found: {example_id}")

    return ExampleMetadata(**load_json(meta_json))


def example_get_content(workspace: Path, zoo_id: str, task_id: str, example_id: str, filename: Optional[str] = None) -> dict:
    """Get example file content"""
    example_path = get_example_path(workspace, zoo_id, task_id, example_id)
    source_files_dir = example_path / "source_files"

    if not source_files_dir.exists():
        raise FileNotFoundError(f"Example not found: {example_id}")

    if filename:
        file_path = source_files_dir / filename
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {filename}")

        content = file_path.read_text(encoding='utf-8')
        return {
            "filename": filename,
            "content": content
        }
    else:
        files = {}
        for file_path in source_files_dir.iterdir():
            if file_path.is_file():
                files[file_path.name] = file_path.read_text(encoding='utf-8')

        return {"files": files}


def example_get_file_map(workspace: Path, zoo_id: str, task_id: str, example_id: str) -> dict:
    """Get compact file map for all files"""
    meta = example_get_meta(workspace, zoo_id, task_id, example_id)

    file_maps = {}
    for file_meta in meta.files:
        file_maps[file_meta.filename] = {
            "lines": file_meta.lines,
            "language": file_meta.language,
            "summary": file_meta.summary,
            "file_map": file_meta.file_map
        }

    return {"file_maps": file_maps}


def example_update_meta(workspace: Path, zoo_id: str, task_id: str, example_id: str, description: Optional[str] = None, tags: Optional[List[str]] = None) -> ExampleMetadata:
    """Update example metadata"""
    example_path = get_example_path(workspace, zoo_id, task_id, example_id)
    meta_json = example_path / "meta.json"

    if not meta_json.exists():
        raise FileNotFoundError(f"Example not found: {example_id}")

    meta = ExampleMetadata(**load_json(meta_json))

    if description is not None:
        meta.description = description
    if tags is not None:
        meta.tags = tags

    meta.updated_at = datetime.utcnow().isoformat() + "Z"

    save_json(meta_json, meta.model_dump())
    return meta


def example_regenerate_meta(workspace: Path, zoo_id: str, task_id: str, example_id: str) -> ExampleMetadata:
    """Re-analyze files and regenerate metadata"""
    example_path = get_example_path(workspace, zoo_id, task_id, example_id)
    meta_json = example_path / "meta.json"
    source_files_dir = example_path / "source_files"

    if not meta_json.exists():
        raise FileNotFoundError(f"Example not found: {example_id}")

    meta = ExampleMetadata(**load_json(meta_json))
    meta.files = []

    for file_path in source_files_dir.iterdir():
        if file_path.is_file():
            content = file_path.read_text(encoding='utf-8')
            relative_path = f"source_files/{file_path.name}"
            file_meta = analyze_file(file_path.name, content, relative_path)
            meta.files.append(file_meta)

    total_lines = sum(f.lines for f in meta.files)
    total_bytes = sum(f.size_bytes for f in meta.files)
    meta.stats = {
        "total_lines": total_lines,
        "total_files": len(meta.files),
        "total_bytes": total_bytes,
        "main_concepts": list(set(concept for f in meta.files for concept in f.key_concepts))[:10]
    }

    meta.updated_at = datetime.utcnow().isoformat() + "Z"

    save_json(meta_json, meta.model_dump())
    return meta


def example_add_file(workspace: Path, zoo_id: str, task_id: str, example_id: str, filename: str, content: str) -> ExampleMetadata:
    """Add file to existing example"""
    example_path = get_example_path(workspace, zoo_id, task_id, example_id)
    meta_json = example_path / "meta.json"
    source_files_dir = example_path / "source_files"

    if not meta_json.exists():
        raise FileNotFoundError(f"Example not found: {example_id}")

    meta = ExampleMetadata(**load_json(meta_json))

    file_path = source_files_dir / filename
    file_path.write_text(content, encoding='utf-8')

    relative_path = f"source_files/{filename}"
    file_meta = analyze_file(filename, content, relative_path)
    meta.files.append(file_meta)

    total_lines = sum(f.lines for f in meta.files)
    total_bytes = sum(f.size_bytes for f in meta.files)
    meta.stats = {
        "total_lines": total_lines,
        "total_files": len(meta.files),
        "total_bytes": total_bytes,
        "main_concepts": list(set(concept for f in meta.files for concept in f.key_concepts))[:10]
    }

    meta.updated_at = datetime.utcnow().isoformat() + "Z"

    save_json(meta_json, meta.model_dump())
    return meta


def example_delete(workspace: Path, zoo_id: str, task_id: str, example_id: str) -> dict:
    """Delete example"""
    example_path = get_example_path(workspace, zoo_id, task_id, example_id)
    meta_json = example_path / "meta.json"

    if not meta_json.exists():
        raise FileNotFoundError(f"Example not found: {example_id}")

    delete_directory(example_path)

    task_path = get_task_path(workspace, zoo_id, task_id)
    task_json = task_path / "task.json"
    if task_json.exists():
        task_meta = TaskMetadata(**load_json(task_json))
        task_meta.example_count = max(0, task_meta.example_count - 1)
        task_meta.updated_at = datetime.utcnow().isoformat() + "Z"
        save_json(task_json, task_meta.model_dump())

    zoo_path = get_zoo_path(workspace, zoo_id)
    zoo_json = zoo_path / "zoo.json"
    if zoo_json.exists():
        zoo_meta = ZooMetadata(**load_json(zoo_json))
        zoo_meta.example_count = max(0, zoo_meta.example_count - 1)
        zoo_meta.updated_at = datetime.utcnow().isoformat() + "Z"
        save_json(zoo_json, zoo_meta.model_dump())

    return {
        "status": "deleted",
        "example_id": example_id
    }


def example_delete_file(workspace: Path, zoo_id: str, task_id: str, example_id: str, filename: str) -> ExampleMetadata:
    """Delete specific file from example"""
    example_path = get_example_path(workspace, zoo_id, task_id, example_id)
    meta_json = example_path / "meta.json"
    source_files_dir = example_path / "source_files"

    if not meta_json.exists():
        raise FileNotFoundError(f"Example not found: {example_id}")

    meta = ExampleMetadata(**load_json(meta_json))

    file_path = source_files_dir / filename
    if file_path.exists():
        file_path.unlink()

    meta.files = [f for f in meta.files if f.filename != filename]

    if meta.files:
        total_lines = sum(f.lines for f in meta.files)
        total_bytes = sum(f.size_bytes for f in meta.files)
        meta.stats = {
            "total_lines": total_lines,
            "total_files": len(meta.files),
            "total_bytes": total_bytes,
            "main_concepts": list(set(concept for f in meta.files for concept in f.key_concepts))[:10]
        }
    else:
        meta.stats = {}

    meta.updated_at = datetime.utcnow().isoformat() + "Z"

    save_json(meta_json, meta.model_dump())
    return meta