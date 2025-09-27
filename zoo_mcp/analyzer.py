import ast
import re
from pathlib import Path
from typing import Optional, List
from zoo_mcp.zoo_models import FileMetadata, FileStructure


LANGUAGE_EXTENSIONS = {
    '.py': 'python',
    '.js': 'javascript',
    '.ts': 'typescript',
    '.jsx': 'javascript',
    '.tsx': 'typescript',
    '.rs': 'rust',
    '.go': 'go',
    '.java': 'java',
    '.c': 'c',
    '.cpp': 'cpp',
    '.h': 'c',
    '.hpp': 'cpp',
    '.cs': 'csharp',
    '.rb': 'ruby',
    '.php': 'php',
    '.swift': 'swift',
    '.kt': 'kotlin',
    '.html': 'html',
    '.css': 'css',
    '.scss': 'scss',
    '.json': 'json',
    '.yaml': 'yaml',
    '.yml': 'yaml',
    '.md': 'markdown',
    '.sh': 'shell',
    '.bash': 'shell',
}


def detect_language(filename: str, content: str = None) -> Optional[str]:
    """Detect programming language from filename/content"""
    ext = Path(filename).suffix.lower()
    return LANGUAGE_EXTENSIONS.get(ext)


def analyze_file(filename: str, content: str, relative_path: str) -> FileMetadata:
    """Analyze file and generate metadata"""
    language = detect_language(filename, content)
    lines = content.count('\n') + 1
    size_bytes = len(content.encode('utf-8'))

    structure = FileStructure()
    if language == 'python':
        structure = extract_structure_python(content)
    elif language in ['javascript', 'typescript']:
        structure = extract_structure_javascript(content)

    file_map = generate_file_map(content, structure)
    dependencies = extract_dependencies(content, language)
    key_concepts = extract_key_concepts(content, language)
    summary = generate_summary(filename, structure, language)

    return FileMetadata(
        filename=filename,
        relative_path=relative_path,
        size_bytes=size_bytes,
        lines=lines,
        language=language,
        summary=summary,
        structure=structure,
        file_map=file_map,
        dependencies=dependencies,
        key_concepts=key_concepts
    )


def extract_structure_python(content: str) -> FileStructure:
    """Extract structure from Python code using AST"""
    structure = FileStructure()

    try:
        tree = ast.parse(content)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    structure.imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    for alias in node.names:
                        structure.imports.append(f"{node.module}.{alias.name}")

        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                methods = [m.name for m in node.body if isinstance(m, ast.FunctionDef)]
                structure.classes.append({
                    "name": node.name,
                    "methods": methods,
                    "line_start": node.lineno,
                    "line_end": node.end_lineno or node.lineno
                })

            elif isinstance(node, ast.FunctionDef):
                params = [arg.arg for arg in node.args.args]
                structure.functions.append({
                    "name": node.name,
                    "params": params,
                    "line_start": node.lineno,
                    "line_end": node.end_lineno or node.lineno
                })

            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id.isupper():
                        structure.constants.append(target.id)

    except SyntaxError:
        pass

    return structure


def extract_structure_javascript(content: str) -> FileStructure:
    """Extract structure from JS/TS code using regex"""
    structure = FileStructure()

    import_pattern = r'import\s+(?:{[^}]+}|[\w\s,*]+)\s+from\s+[\'"]([^\'"]+)[\'"]'
    imports = re.findall(import_pattern, content)
    structure.imports = list(set(imports))

    export_pattern = r'export\s+(?:default\s+)?(?:class|function|const|let|var)\s+(\w+)'
    exports = re.findall(export_pattern, content)
    structure.exports = list(set(exports))

    class_pattern = r'class\s+(\w+)'
    classes = re.findall(class_pattern, content)
    for class_name in classes:
        method_section = re.search(rf'class\s+{class_name}.*?{{(.*?)}}', content, re.DOTALL)
        methods = []
        if method_section:
            method_pattern = r'(\w+)\s*\([^)]*\)\s*{'
            methods = re.findall(method_pattern, method_section.group(1))

        lines = content[:content.find(f'class {class_name}')].count('\n') + 1
        structure.classes.append({
            "name": class_name,
            "methods": methods,
            "line_start": lines,
            "line_end": lines
        })

    func_pattern = r'function\s+(\w+)\s*\(([^)]*)\)'
    functions = re.findall(func_pattern, content)
    for func_name, params in functions:
        param_list = [p.strip().split('=')[0].strip() for p in params.split(',') if p.strip()]
        lines = content[:content.find(f'function {func_name}')].count('\n') + 1
        structure.functions.append({
            "name": func_name,
            "params": param_list,
            "line_start": lines,
            "line_end": lines
        })

    arrow_func_pattern = r'const\s+(\w+)\s*=\s*\([^)]*\)\s*=>'
    arrow_funcs = re.findall(arrow_func_pattern, content)
    for func_name in arrow_funcs:
        lines = content[:content.find(f'const {func_name}')].count('\n') + 1
        structure.functions.append({
            "name": func_name,
            "params": [],
            "line_start": lines,
            "line_end": lines
        })

    const_pattern = r'const\s+([A-Z_][A-Z0-9_]*)\s*='
    constants = re.findall(const_pattern, content)
    structure.constants = list(set(constants))

    return structure


def generate_file_map(content: str, structure: FileStructure) -> List[str]:
    """Generate line-range outline of file"""
    lines = content.split('\n')
    file_map = []

    if structure.imports:
        file_map.append("1-10: Imports and dependencies")

    for cls in structure.classes:
        start = cls.get("line_start", 0)
        end = cls.get("line_end", start)
        methods_str = ", ".join(cls.get("methods", [])[:3])
        if len(cls.get("methods", [])) > 3:
            methods_str += "..."
        file_map.append(f"{start}-{end}: {cls['name']} class ({methods_str})")

    for func in structure.functions:
        start = func.get("line_start", 0)
        end = func.get("line_end", start)
        params_str = ", ".join(func.get("params", [])[:3])
        file_map.append(f"{start}-{end}: {func['name']}({params_str})")

    if not file_map:
        mid = len(lines) // 2
        file_map = [
            f"1-{mid}: First half",
            f"{mid+1}-{len(lines)}: Second half"
        ]

    return file_map


def extract_dependencies(content: str, language: Optional[str]) -> List[str]:
    """Extract imported packages/modules"""
    dependencies = set()

    if language == 'python':
        import_pattern = r'(?:from|import)\s+(\w+)'
        matches = re.findall(import_pattern, content)
        dependencies.update(matches)

    elif language in ['javascript', 'typescript']:
        import_pattern = r'from\s+[\'"]([^\'"]+)[\'"]'
        matches = re.findall(import_pattern, content)
        dependencies.update([m.split('/')[0] for m in matches if not m.startswith('.')])

        require_pattern = r'require\([\'"]([^\'"]+)[\'"]\)'
        matches = re.findall(require_pattern, content)
        dependencies.update([m.split('/')[0] for m in matches if not m.startswith('.')])

    return sorted(list(dependencies))[:10]


def extract_key_concepts(content: str, language: Optional[str]) -> List[str]:
    """Extract algorithm/pattern keywords"""
    concepts = set()

    keywords = [
        'async', 'await', 'promise', 'callback', 'event', 'stream', 'buffer',
        'cache', 'queue', 'stack', 'tree', 'graph', 'hash', 'map', 'set',
        'sort', 'search', 'binary', 'recursive', 'iterate', 'loop',
        'api', 'http', 'rest', 'graphql', 'websocket', 'socket',
        'database', 'sql', 'query', 'transaction',
        'auth', 'token', 'jwt', 'oauth',
        'encrypt', 'decrypt', 'hash', 'crypto',
        'test', 'mock', 'stub', 'spy',
        'render', 'component', 'state', 'props', 'hook',
        'route', 'middleware', 'controller', 'model', 'view',
        'noise', 'perlin', 'simplex', 'procedural', 'terrain', 'heightmap',
        'shader', 'vertex', 'fragment', 'mesh', 'geometry', 'buffer',
        'matrix', 'vector', 'quaternion', 'transform'
    ]

    content_lower = content.lower()
    for keyword in keywords:
        if keyword in content_lower:
            concepts.add(keyword)

    return sorted(list(concepts))[:10]


def generate_summary(filename: str, structure: FileStructure, language: Optional[str]) -> str:
    """Generate 1-2 sentence file summary"""
    parts = []

    if structure.classes:
        class_names = [c['name'] for c in structure.classes[:2]]
        parts.append(f"Defines {', '.join(class_names)}")

    if structure.functions:
        func_count = len(structure.functions)
        if func_count <= 3:
            func_names = [f['name'] for f in structure.functions]
            parts.append(f"implements {', '.join(func_names)}")
        else:
            parts.append(f"implements {func_count} functions")

    if structure.exports:
        export_names = structure.exports[:2]
        parts.append(f"exports {', '.join(export_names)}")

    if parts:
        return f"{Path(filename).stem} - {' and '.join(parts)}"
    else:
        return f"{Path(filename).stem} - {language or 'code'} file"