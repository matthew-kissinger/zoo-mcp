import json
from pathlib import Path
from typing import Optional
from zoo_mcp.zoo_models import ZooMetadata, TaskMetadata, ExampleMetadata
from zoo_mcp.storage import (
    get_zoo_path,
    get_task_path,
    get_example_path,
    load_json,
    save_json,
    list_subdirs,
)


def zoo_export_json(workspace: Path, zoo_id: str, include_content: bool = True, output_path: Optional[str] = None) -> dict:
    """Export zoo to JSON (backup/share format)"""
    zoo_path = get_zoo_path(workspace, zoo_id)
    zoo_json = zoo_path / "zoo.json"

    if not zoo_json.exists():
        raise FileNotFoundError(f"Zoo not found: {zoo_id}")

    zoo_meta = ZooMetadata(**load_json(zoo_json))

    export_data = {
        "version": "1.0",
        "zoo": zoo_meta.model_dump(),
        "tasks": []
    }

    tasks_dir = zoo_path / "tasks"
    if tasks_dir.exists():
        for task_dir in list_subdirs(tasks_dir):
            task_json = task_dir / "task.json"
            if task_json.exists():
                task_meta = TaskMetadata(**load_json(task_json))
                task_data = {
                    "task": task_meta.model_dump(),
                    "examples": []
                }

                examples_dir = task_dir / "examples"
                if examples_dir.exists():
                    for example_dir in list_subdirs(examples_dir):
                        meta_json = example_dir / "meta.json"
                        if meta_json.exists():
                            example_meta = ExampleMetadata(**load_json(meta_json))
                            example_data = example_meta.model_dump()

                            if include_content:
                                source_files_dir = example_dir / "source_files"
                                files_content = {}
                                if source_files_dir.exists():
                                    for file_path in source_files_dir.iterdir():
                                        if file_path.is_file():
                                            try:
                                                content = file_path.read_text(encoding='utf-8')
                                                files_content[file_path.name] = content
                                            except Exception:
                                                pass

                                example_data["_content"] = files_content

                            task_data["examples"].append(example_data)

                export_data["tasks"].append(task_data)

    if output_path:
        output_file = Path(output_path).resolve()
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        return {
            "status": "exported",
            "output_path": str(output_file),
            "size_bytes": output_file.stat().st_size
        }
    else:
        default_path = workspace / f"zoo_export_{zoo_id}.json"
        with open(default_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        return {
            "status": "exported",
            "output_path": str(default_path),
            "size_bytes": default_path.stat().st_size
        }


def zoo_export_markdown(workspace: Path, zoo_id: str, include_code_samples: bool = False, output_path: Optional[str] = None) -> dict:
    """Export zoo to markdown index (documentation)"""
    zoo_path = get_zoo_path(workspace, zoo_id)
    zoo_json = zoo_path / "zoo.json"

    if not zoo_json.exists():
        raise FileNotFoundError(f"Zoo not found: {zoo_id}")

    zoo_meta = ZooMetadata(**load_json(zoo_json))

    md_lines = []
    md_lines.append(f"# {zoo_meta.name}\n")
    md_lines.append(f"{zoo_meta.description}\n")
    md_lines.append(f"\n**Tags:** {', '.join(zoo_meta.tags)}\n")
    md_lines.append(f"\n**Created:** {zoo_meta.created_at}")
    md_lines.append(f"**Tasks:** {zoo_meta.task_count} | **Examples:** {zoo_meta.example_count}\n")
    md_lines.append("\n---\n")

    tasks_dir = zoo_path / "tasks"
    if tasks_dir.exists():
        for task_dir in sorted(list_subdirs(tasks_dir)):
            task_json = task_dir / "task.json"
            if task_json.exists():
                task_meta = TaskMetadata(**load_json(task_json))

                md_lines.append(f"\n## {task_meta.name}\n")
                md_lines.append(f"{task_meta.description}\n")
                md_lines.append(f"\n**Tags:** {', '.join(task_meta.tags)} | **Status:** {task_meta.status}\n")

                examples_dir = task_dir / "examples"
                if examples_dir.exists():
                    examples = list(list_subdirs(examples_dir))
                    if examples:
                        md_lines.append(f"\n### Examples ({len(examples)})\n")

                        for example_dir in examples:
                            meta_json = example_dir / "meta.json"
                            if meta_json.exists():
                                example_meta = ExampleMetadata(**load_json(meta_json))

                                md_lines.append(f"\n#### {example_meta.id}\n")
                                md_lines.append(f"{example_meta.description}\n")
                                md_lines.append(f"\n- **Source:** {example_meta.source_type} ({example_meta.source_tool})")
                                md_lines.append(f"- **URL:** {example_meta.source_url}")
                                md_lines.append(f"- **Language:** {example_meta.language}")
                                md_lines.append(f"- **Tags:** {', '.join(example_meta.tags)}")
                                md_lines.append(f"- **Files:** {len(example_meta.files)} ({example_meta.stats.get('total_lines', 0)} lines)\n")

                                if example_meta.files:
                                    md_lines.append("\n**File Map:**\n")
                                    for file_meta in example_meta.files:
                                        md_lines.append(f"\n- `{file_meta.filename}` ({file_meta.lines} lines): {file_meta.summary}")
                                        if file_meta.file_map:
                                            for map_entry in file_meta.file_map[:3]:
                                                md_lines.append(f"  - {map_entry}")

                                if include_code_samples and example_meta.files:
                                    source_files_dir = example_dir / "source_files"
                                    for file_meta in example_meta.files[:1]:
                                        file_path = source_files_dir / file_meta.filename
                                        if file_path.exists():
                                            content = file_path.read_text(encoding='utf-8')
                                            lang = file_meta.language or ""
                                            md_lines.append(f"\n```{lang}")
                                            md_lines.append(content[:500])
                                            if len(content) > 500:
                                                md_lines.append("\n... (truncated)")
                                            md_lines.append("```\n")

    markdown_content = '\n'.join(md_lines)

    if output_path:
        output_file = Path(output_path).resolve()
        output_file.write_text(markdown_content, encoding='utf-8')

        return {
            "status": "exported",
            "output_path": str(output_file),
            "size_bytes": output_file.stat().st_size
        }
    else:
        default_path = workspace / f"zoo_index_{zoo_id}.md"
        default_path.write_text(markdown_content, encoding='utf-8')

        return {
            "status": "exported",
            "output_path": str(default_path),
            "size_bytes": default_path.stat().st_size
        }


def zoo_import_json(workspace: Path, input_path: str) -> ZooMetadata:
    """Import zoo from JSON export"""
    from zoo_mcp.tools.zoo_crud import zoo_create
    from zoo_mcp.tools.task_crud import task_create
    from zoo_mcp.adapters.example_committer import commit_from_content

    input_file = Path(input_path).resolve()

    if not input_file.exists():
        raise FileNotFoundError(f"Import file not found: {input_path}")

    with open(input_file, 'r', encoding='utf-8') as f:
        import_data = json.load(f)

    zoo_data = import_data.get("zoo", {})

    zoo_meta = zoo_create(
        workspace,
        name=zoo_data["name"],
        description=zoo_data["description"],
        tags=zoo_data.get("tags", [])
    )

    for task_data in import_data.get("tasks", []):
        task_info = task_data.get("task", {})

        task_meta = task_create(
            workspace,
            zoo_id=zoo_meta.id,
            name=task_info["name"],
            description=task_info["description"],
            tags=task_info.get("tags", [])
        )

        for example_data in task_data.get("examples", []):
            files_content = example_data.pop("_content", {})

            if files_content:
                for filename, content in files_content.items():
                    commit_from_content(
                        workspace=workspace,
                        zoo_id=zoo_meta.id,
                        task_id=task_meta.id,
                        filename=filename,
                        content=content,
                        language=example_data.get("language"),
                        description=example_data["description"],
                        tags=example_data.get("tags", []),
                        source_url=example_data.get("source_url")
                    )
                    break

    return zoo_meta


def zoo_get_index(workspace: Path, zoo_id: str, include_tasks: bool = True, include_examples: bool = True) -> dict:
    """Get hierarchical summary of zoo (context-efficient)"""
    zoo_path = get_zoo_path(workspace, zoo_id)
    zoo_json = zoo_path / "zoo.json"

    if not zoo_json.exists():
        raise FileNotFoundError(f"Zoo not found: {zoo_id}")

    zoo_meta = ZooMetadata(**load_json(zoo_json))

    index = {
        "zoo": {
            "id": zoo_meta.id,
            "name": zoo_meta.name,
            "description": zoo_meta.description,
            "tags": zoo_meta.tags,
            "task_count": zoo_meta.task_count,
            "example_count": zoo_meta.example_count
        }
    }

    if include_tasks:
        tasks = []
        tasks_dir = zoo_path / "tasks"
        if tasks_dir.exists():
            for task_dir in list_subdirs(tasks_dir):
                task_json = task_dir / "task.json"
                if task_json.exists():
                    task_meta = TaskMetadata(**load_json(task_json))
                    task_summary = {
                        "id": task_meta.id,
                        "name": task_meta.name,
                        "description": task_meta.description,
                        "tags": task_meta.tags,
                        "status": task_meta.status,
                        "example_count": task_meta.example_count
                    }

                    if include_examples:
                        examples = []
                        examples_dir = task_dir / "examples"
                        if examples_dir.exists():
                            for example_dir in list_subdirs(examples_dir):
                                meta_json = example_dir / "meta.json"
                                if meta_json.exists():
                                    example_meta = ExampleMetadata(**load_json(meta_json))
                                    examples.append({
                                        "id": example_meta.id,
                                        "description": example_meta.description,
                                        "language": example_meta.language,
                                        "file_count": len(example_meta.files),
                                        "total_lines": example_meta.stats.get("total_lines", 0)
                                    })

                        task_summary["examples"] = examples

                    tasks.append(task_summary)

        index["tasks"] = tasks

    return index