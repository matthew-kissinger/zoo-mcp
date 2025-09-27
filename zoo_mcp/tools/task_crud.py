from datetime import datetime
from pathlib import Path
from typing import List, Optional
from zoo_mcp.zoo_models import TaskMetadata, ZooMetadata, ExampleMetadata
from zoo_mcp.storage import (
    get_zoo_path,
    get_task_path,
    load_json,
    save_json,
    generate_id,
    list_subdirs,
    delete_directory,
)


def task_create(workspace: Path, zoo_id: str, name: str, description: str, tags: Optional[List[str]] = None) -> TaskMetadata:
    """Create task in zoo"""
    zoo_path = get_zoo_path(workspace, zoo_id)
    zoo_json = zoo_path / "zoo.json"

    if not zoo_json.exists():
        raise FileNotFoundError(f"Zoo not found: {zoo_id}")

    task_id = generate_id()
    now = datetime.utcnow().isoformat() + "Z"

    task_meta = TaskMetadata(
        id=task_id,
        zoo_id=zoo_id,
        name=name,
        description=description,
        status="active",
        tags=tags or [],
        created_at=now,
        updated_at=now,
        example_count=0
    )

    task_path = get_task_path(workspace, zoo_id, task_id)
    task_path.mkdir(parents=True, exist_ok=True)

    examples_dir = task_path / "examples"
    examples_dir.mkdir(exist_ok=True)

    task_json_path = task_path / "task.json"
    save_json(task_json_path, task_meta.model_dump())

    zoo_meta = ZooMetadata(**load_json(zoo_json))
    zoo_meta.task_count += 1
    zoo_meta.updated_at = now
    save_json(zoo_json, zoo_meta.model_dump())

    return task_meta


def task_list(workspace: Path, zoo_id: str, status_filter: Optional[str] = None) -> List[TaskMetadata]:
    """List tasks in zoo"""
    zoo_path = get_zoo_path(workspace, zoo_id)
    tasks_dir = zoo_path / "tasks"

    if not tasks_dir.exists():
        return []

    tasks = []
    for task_dir in list_subdirs(tasks_dir):
        task_json = task_dir / "task.json"
        if task_json.exists():
            try:
                data = load_json(task_json)
                task_meta = TaskMetadata(**data)

                if status_filter is None or task_meta.status == status_filter:
                    tasks.append(task_meta)
            except Exception:
                pass

    return sorted(tasks, key=lambda t: t.created_at, reverse=True)


def task_get(workspace: Path, zoo_id: str, task_id: str, include_examples: bool = False) -> dict:
    """Get task details"""
    task_path = get_task_path(workspace, zoo_id, task_id)
    task_json = task_path / "task.json"

    if not task_json.exists():
        raise FileNotFoundError(f"Task not found: {task_id}")

    task_meta = TaskMetadata(**load_json(task_json))

    result = {"task": task_meta}

    if include_examples:
        examples_dir = task_path / "examples"
        examples = []

        if examples_dir.exists():
            for example_dir in list_subdirs(examples_dir):
                meta_json = example_dir / "meta.json"
                if meta_json.exists():
                    try:
                        data = load_json(meta_json)
                        summary = {
                            "id": data["id"],
                            "description": data["description"],
                            "tags": data["tags"],
                            "language": data.get("language"),
                            "source_type": data["source_type"],
                            "file_count": len(data.get("files", [])),
                        }
                        examples.append(summary)
                    except Exception:
                        pass

        result["examples"] = sorted(examples, key=lambda e: e["id"])

    return result


def task_update(workspace: Path, zoo_id: str, task_id: str, name: Optional[str] = None, description: Optional[str] = None, status: Optional[str] = None, tags: Optional[List[str]] = None) -> TaskMetadata:
    """Update task metadata"""
    task_path = get_task_path(workspace, zoo_id, task_id)
    task_json = task_path / "task.json"

    if not task_json.exists():
        raise FileNotFoundError(f"Task not found: {task_id}")

    task_meta = TaskMetadata(**load_json(task_json))

    if name is not None:
        task_meta.name = name
    if description is not None:
        task_meta.description = description
    if status is not None:
        task_meta.status = status
    if tags is not None:
        task_meta.tags = tags

    task_meta.updated_at = datetime.utcnow().isoformat() + "Z"

    save_json(task_json, task_meta.model_dump())

    zoo_path = get_zoo_path(workspace, zoo_id)
    zoo_json = zoo_path / "zoo.json"
    if zoo_json.exists():
        zoo_meta = ZooMetadata(**load_json(zoo_json))
        zoo_meta.updated_at = task_meta.updated_at
        save_json(zoo_json, zoo_meta.model_dump())

    return task_meta


def task_delete(workspace: Path, zoo_id: str, task_id: str) -> dict:
    """Delete task and all examples"""
    task_path = get_task_path(workspace, zoo_id, task_id)
    task_json = task_path / "task.json"

    if not task_json.exists():
        raise FileNotFoundError(f"Task not found: {task_id}")

    task_meta = TaskMetadata(**load_json(task_json))
    example_count = task_meta.example_count

    delete_directory(task_path)

    zoo_path = get_zoo_path(workspace, zoo_id)
    zoo_json = zoo_path / "zoo.json"
    if zoo_json.exists():
        zoo_meta = ZooMetadata(**load_json(zoo_json))
        zoo_meta.task_count = max(0, zoo_meta.task_count - 1)
        zoo_meta.example_count = max(0, zoo_meta.example_count - example_count)
        zoo_meta.updated_at = datetime.utcnow().isoformat() + "Z"
        save_json(zoo_json, zoo_meta.model_dump())

    return {
        "status": "deleted",
        "task_id": task_id,
        "examples_deleted": example_count
    }