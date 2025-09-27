import json
import uuid
from pathlib import Path
from typing import Optional
from zoo_mcp.guards import safe_path_join, ensure_workspace


def init_storage(workspace_path: Path) -> Path:
    """Initialize zoo storage directory structure"""
    workspace = ensure_workspace(str(workspace_path))
    zoos_dir = workspace / "zoos"
    zoos_dir.mkdir(parents=True, exist_ok=True)
    return zoos_dir


def get_zoo_path(workspace: Path, zoo_id: str) -> Path:
    """Get path to zoo directory"""
    zoos_dir = workspace / "zoos"
    return safe_path_join(zoos_dir, zoo_id)


def get_task_path(workspace: Path, zoo_id: str, task_id: str) -> Path:
    """Get path to task directory"""
    zoo_path = get_zoo_path(workspace, zoo_id)
    tasks_dir = zoo_path / "tasks"
    return safe_path_join(tasks_dir, task_id)


def get_example_path(workspace: Path, zoo_id: str, task_id: str, example_id: str) -> Path:
    """Get path to example directory"""
    task_path = get_task_path(workspace, zoo_id, task_id)
    examples_dir = task_path / "examples"
    return safe_path_join(examples_dir, example_id)


def load_json(file_path: Path) -> dict:
    """Load JSON file with error handling"""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {file_path}: {e}")


def save_json(file_path: Path, data: dict) -> None:
    """Save JSON file with atomic write"""
    file_path.parent.mkdir(parents=True, exist_ok=True)

    temp_path = file_path.with_suffix('.tmp')
    try:
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        temp_path.replace(file_path)
    except Exception as e:
        if temp_path.exists():
            temp_path.unlink()
        raise e


def generate_id(prefix: str = "") -> str:
    """Generate unique ID (e.g., 'ex_abc123')"""
    unique_part = str(uuid.uuid4())[:8]
    if prefix:
        return f"{prefix}_{unique_part}"
    return unique_part


def list_subdirs(directory: Path) -> list[Path]:
    """List all subdirectories in a directory"""
    if not directory.exists():
        return []
    return [d for d in directory.iterdir() if d.is_dir()]


def delete_directory(directory: Path) -> None:
    """Recursively delete directory"""
    if not directory.exists():
        return

    for item in directory.iterdir():
        if item.is_dir():
            delete_directory(item)
        else:
            item.unlink()

    directory.rmdir()


def get_directory_size(directory: Path) -> int:
    """Get total size of directory in bytes"""
    total = 0
    for item in directory.rglob('*'):
        if item.is_file():
            total += item.stat().st_size
    return total


def count_files(directory: Path, extension: Optional[str] = None) -> int:
    """Count files in directory, optionally filtered by extension"""
    if not directory.exists():
        return 0

    if extension:
        return len(list(directory.rglob(f'*{extension}')))
    else:
        return len([f for f in directory.rglob('*') if f.is_file()])