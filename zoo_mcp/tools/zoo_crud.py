from datetime import datetime
from pathlib import Path
from typing import List, Optional
from zoo_mcp.zoo_models import ZooMetadata, TaskMetadata
from zoo_mcp.storage import (
    get_zoo_path,
    load_json,
    save_json,
    generate_id,
    list_subdirs,
    delete_directory,
)


def zoo_create(workspace: Path, name: str, description: str, tags: Optional[List[str]] = None) -> ZooMetadata:
    """Create new zoo"""
    zoo_id = generate_id()
    now = datetime.utcnow().isoformat() + "Z"

    zoo_meta = ZooMetadata(
        id=zoo_id,
        name=name,
        description=description,
        tags=tags or [],
        created_at=now,
        updated_at=now,
        task_count=0,
        example_count=0
    )

    zoo_path = get_zoo_path(workspace, zoo_id)
    zoo_path.mkdir(parents=True, exist_ok=True)

    tasks_dir = zoo_path / "tasks"
    tasks_dir.mkdir(exist_ok=True)

    zoo_json_path = zoo_path / "zoo.json"
    save_json(zoo_json_path, zoo_meta.model_dump())

    return zoo_meta


def zoo_list(workspace: Path) -> List[ZooMetadata]:
    """List all zoos"""
    zoos_dir = workspace / "zoos"
    if not zoos_dir.exists():
        return []

    zoos = []
    for zoo_dir in list_subdirs(zoos_dir):
        zoo_json = zoo_dir / "zoo.json"
        if zoo_json.exists():
            try:
                data = load_json(zoo_json)
                zoos.append(ZooMetadata(**data))
            except Exception:
                pass

    return sorted(zoos, key=lambda z: z.created_at, reverse=True)


def zoo_get(workspace: Path, zoo_id: str) -> dict:
    """Get zoo with task list"""
    zoo_path = get_zoo_path(workspace, zoo_id)
    zoo_json = zoo_path / "zoo.json"

    if not zoo_json.exists():
        raise FileNotFoundError(f"Zoo not found: {zoo_id}")

    zoo_meta = ZooMetadata(**load_json(zoo_json))

    tasks_dir = zoo_path / "tasks"
    tasks = []
    if tasks_dir.exists():
        for task_dir in list_subdirs(tasks_dir):
            task_json = task_dir / "task.json"
            if task_json.exists():
                try:
                    data = load_json(task_json)
                    tasks.append(TaskMetadata(**data))
                except Exception:
                    pass

    tasks = sorted(tasks, key=lambda t: t.created_at, reverse=True)

    return {
        "zoo": zoo_meta,
        "tasks": tasks
    }


def zoo_update(workspace: Path, zoo_id: str, name: Optional[str] = None, description: Optional[str] = None, tags: Optional[List[str]] = None) -> ZooMetadata:
    """Update zoo metadata"""
    zoo_path = get_zoo_path(workspace, zoo_id)
    zoo_json = zoo_path / "zoo.json"

    if not zoo_json.exists():
        raise FileNotFoundError(f"Zoo not found: {zoo_id}")

    zoo_meta = ZooMetadata(**load_json(zoo_json))

    if name is not None:
        zoo_meta.name = name
    if description is not None:
        zoo_meta.description = description
    if tags is not None:
        zoo_meta.tags = tags

    zoo_meta.updated_at = datetime.utcnow().isoformat() + "Z"

    save_json(zoo_json, zoo_meta.model_dump())
    return zoo_meta


def zoo_delete(workspace: Path, zoo_id: str) -> dict:
    """Delete zoo and all contents"""
    zoo_path = get_zoo_path(workspace, zoo_id)

    if not zoo_path.exists():
        raise FileNotFoundError(f"Zoo not found: {zoo_id}")

    delete_directory(zoo_path)

    return {
        "status": "deleted",
        "zoo_id": zoo_id
    }


def zoo_search(workspace: Path, query: str) -> List[ZooMetadata]:
    """Search zoos by name/description/tags"""
    all_zoos = zoo_list(workspace)
    query_lower = query.lower()

    matching_zoos = []
    for zoo in all_zoos:
        if (query_lower in zoo.name.lower() or
            query_lower in zoo.description.lower() or
            any(query_lower in tag.lower() for tag in zoo.tags)):
            matching_zoos.append(zoo)

    return matching_zoos