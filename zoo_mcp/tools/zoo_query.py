import re
from pathlib import Path
from typing import List, Optional
from zoo_mcp.storage import (
    get_zoo_path,
    get_task_path,
    get_example_path,
    load_json,
    list_subdirs,
)


def zoo_grep(workspace: Path, zoo_id: str, pattern: str, language: Optional[str] = None, task_filter: Optional[str] = None, flags: str = "i", max_results: int = 100) -> List[dict]:
    """Grep across all examples in zoo"""
    zoo_path = get_zoo_path(workspace, zoo_id)
    tasks_dir = zoo_path / "tasks"

    if not tasks_dir.exists():
        return []

    results = []
    regex_flags = 0
    if 'i' in flags:
        regex_flags |= re.IGNORECASE
    if 'm' in flags:
        regex_flags |= re.MULTILINE
    if 's' in flags:
        regex_flags |= re.DOTALL

    try:
        compiled_pattern = re.compile(pattern, regex_flags)
    except re.error as e:
        raise ValueError(f"Invalid regex pattern: {e}")

    for task_dir in list_subdirs(tasks_dir):
        task_id = task_dir.name

        if task_filter and task_id != task_filter:
            continue

        task_results = task_grep(workspace, zoo_id, task_id, pattern, language, flags, max_results - len(results))
        results.extend(task_results)

        if len(results) >= max_results:
            break

    return results[:max_results]


def task_grep(workspace: Path, zoo_id: str, task_id: str, pattern: str, language: Optional[str] = None, flags: str = "i", max_results: int = 100) -> List[dict]:
    """Grep across all examples in task"""
    task_path = get_task_path(workspace, zoo_id, task_id)
    examples_dir = task_path / "examples"

    if not examples_dir.exists():
        return []

    results = []
    regex_flags = 0
    if 'i' in flags:
        regex_flags |= re.IGNORECASE
    if 'm' in flags:
        regex_flags |= re.MULTILINE
    if 's' in flags:
        regex_flags |= re.DOTALL

    try:
        compiled_pattern = re.compile(pattern, regex_flags)
    except re.error as e:
        raise ValueError(f"Invalid regex pattern: {e}")

    for example_dir in list_subdirs(examples_dir):
        example_id = example_dir.name
        meta_json = example_dir / "meta.json"

        if not meta_json.exists():
            continue

        try:
            meta = load_json(meta_json)

            if language and meta.get("language") != language:
                continue

            example_results = example_grep(workspace, zoo_id, task_id, example_id, pattern, flags)
            results.extend(example_results)

            if len(results) >= max_results:
                break
        except Exception:
            continue

    return results[:max_results]


def example_grep(workspace: Path, zoo_id: str, task_id: str, example_id: str, pattern: str, flags: str = "i") -> List[dict]:
    """Grep within single example"""
    example_path = get_example_path(workspace, zoo_id, task_id, example_id)
    source_files_dir = example_path / "source_files"

    if not source_files_dir.exists():
        return []

    results = []
    regex_flags = 0
    if 'i' in flags:
        regex_flags |= re.IGNORECASE
    if 'm' in flags:
        regex_flags |= re.MULTILINE
    if 's' in flags:
        regex_flags |= re.DOTALL

    try:
        compiled_pattern = re.compile(pattern, regex_flags)
    except re.error as e:
        raise ValueError(f"Invalid regex pattern: {e}")

    for file_path in source_files_dir.iterdir():
        if file_path.is_file():
            try:
                content = file_path.read_text(encoding='utf-8')
                lines = content.split('\n')

                for line_num, line_content in enumerate(lines, start=1):
                    match = compiled_pattern.search(line_content)
                    if match:
                        results.append({
                            "zoo_id": zoo_id,
                            "task_id": task_id,
                            "example_id": example_id,
                            "filename": file_path.name,
                            "line_num": line_num,
                            "line_content": line_content.strip(),
                            "match": match.group(0)
                        })
            except Exception:
                continue

    return results


def zoo_search_examples(workspace: Path, zoo_id: str, query: str) -> List[dict]:
    """Search example descriptions/tags/filenames"""
    zoo_path = get_zoo_path(workspace, zoo_id)
    tasks_dir = zoo_path / "tasks"

    if not tasks_dir.exists():
        return []

    query_lower = query.lower()
    results = []

    for task_dir in list_subdirs(tasks_dir):
        task_id = task_dir.name
        examples_dir = task_dir / "examples"

        if not examples_dir.exists():
            continue

        for example_dir in list_subdirs(examples_dir):
            meta_json = example_dir / "meta.json"

            if not meta_json.exists():
                continue

            try:
                meta = load_json(meta_json)

                matches = False
                if query_lower in meta.get("description", "").lower():
                    matches = True
                elif any(query_lower in tag.lower() for tag in meta.get("tags", [])):
                    matches = True
                elif any(query_lower in f.get("filename", "").lower() for f in meta.get("files", [])):
                    matches = True

                if matches:
                    results.append({
                        "zoo_id": zoo_id,
                        "task_id": task_id,
                        "example_id": meta["id"],
                        "description": meta["description"],
                        "tags": meta["tags"],
                        "language": meta.get("language"),
                        "source_url": meta["source_url"]
                    })
            except Exception:
                continue

    return results


def example_find_by_concept(workspace: Path, zoo_id: str, task_id: str, concept: str) -> List[dict]:
    """Find examples by key concept"""
    task_path = get_task_path(workspace, zoo_id, task_id)
    examples_dir = task_path / "examples"

    if not examples_dir.exists():
        return []

    concept_lower = concept.lower()
    results = []

    for example_dir in list_subdirs(examples_dir):
        meta_json = example_dir / "meta.json"

        if not meta_json.exists():
            continue

        try:
            meta = load_json(meta_json)

            main_concepts = meta.get("stats", {}).get("main_concepts", [])
            if any(concept_lower in c.lower() for c in main_concepts):
                results.append({
                    "example_id": meta["id"],
                    "description": meta["description"],
                    "tags": meta["tags"],
                    "main_concepts": main_concepts,
                    "source_url": meta["source_url"]
                })
        except Exception:
            continue

    return results


def example_get_function(workspace: Path, zoo_id: str, task_id: str, example_id: str, function_name: str) -> dict:
    """Extract specific function from example"""
    example_path = get_example_path(workspace, zoo_id, task_id, example_id)
    meta_json = example_path / "meta.json"
    source_files_dir = example_path / "source_files"

    if not meta_json.exists():
        raise FileNotFoundError(f"Example not found: {example_id}")

    meta = load_json(meta_json)

    for file_meta in meta.get("files", []):
        for func in file_meta.get("structure", {}).get("functions", []):
            if func["name"] == function_name:
                filename = file_meta["filename"]
                file_path = source_files_dir / filename

                if file_path.exists():
                    content = file_path.read_text(encoding='utf-8')
                    lines = content.split('\n')

                    start = func.get("line_start", 1) - 1
                    end = func.get("line_end", len(lines))

                    function_code = '\n'.join(lines[start:end])

                    return {
                        "function_name": function_name,
                        "filename": filename,
                        "line_start": func.get("line_start"),
                        "line_end": func.get("line_end"),
                        "params": func.get("params", []),
                        "code": function_code
                    }

    raise ValueError(f"Function '{function_name}' not found in example")


def example_get_class(workspace: Path, zoo_id: str, task_id: str, example_id: str, class_name: str) -> dict:
    """Extract specific class from example"""
    example_path = get_example_path(workspace, zoo_id, task_id, example_id)
    meta_json = example_path / "meta.json"
    source_files_dir = example_path / "source_files"

    if not meta_json.exists():
        raise FileNotFoundError(f"Example not found: {example_id}")

    meta = load_json(meta_json)

    for file_meta in meta.get("files", []):
        for cls in file_meta.get("structure", {}).get("classes", []):
            if cls["name"] == class_name:
                filename = file_meta["filename"]
                file_path = source_files_dir / filename

                if file_path.exists():
                    content = file_path.read_text(encoding='utf-8')
                    lines = content.split('\n')

                    start = cls.get("line_start", 1) - 1
                    end = cls.get("line_end", len(lines))

                    class_code = '\n'.join(lines[start:end])

                    return {
                        "class_name": class_name,
                        "filename": filename,
                        "line_start": cls.get("line_start"),
                        "line_end": cls.get("line_end"),
                        "methods": cls.get("methods", []),
                        "code": class_code
                    }

    raise ValueError(f"Class '{class_name}' not found in example")


def example_get_snippet(workspace: Path, zoo_id: str, task_id: str, example_id: str, filename: str, start_line: int, end_line: int) -> dict:
    """Get specific line range from file"""
    example_path = get_example_path(workspace, zoo_id, task_id, example_id)
    source_files_dir = example_path / "source_files"

    file_path = source_files_dir / filename

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {filename}")

    content = file_path.read_text(encoding='utf-8')
    lines = content.split('\n')

    start = max(0, start_line - 1)
    end = min(len(lines), end_line)

    snippet = '\n'.join(lines[start:end])

    return {
        "filename": filename,
        "start_line": start_line,
        "end_line": end_line,
        "code": snippet
    }