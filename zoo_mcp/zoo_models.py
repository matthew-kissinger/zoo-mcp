from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class ZooMetadata(BaseModel):
    id: str
    name: str
    description: str
    tags: List[str] = []
    created_at: str
    updated_at: str
    task_count: int = 0
    example_count: int = 0


class TaskMetadata(BaseModel):
    id: str
    zoo_id: str
    name: str
    description: str
    status: Literal["active", "archived", "completed"] = "active"
    tags: List[str] = []
    created_at: str
    updated_at: str
    example_count: int = 0


class FileStructure(BaseModel):
    imports: List[str] = []
    exports: List[str] = []
    classes: List[dict] = []
    functions: List[dict] = []
    constants: List[str] = []


class FileMetadata(BaseModel):
    filename: str
    relative_path: str
    size_bytes: int
    lines: int
    language: Optional[str] = None
    summary: str
    structure: FileStructure = Field(default_factory=FileStructure)
    file_map: List[str] = []
    dependencies: List[str] = []
    key_concepts: List[str] = []


class ExampleMetadata(BaseModel):
    id: str
    task_id: str
    source_type: str
    source_tool: str
    source_url: str
    repo: Optional[str] = None
    ref: Optional[str] = None
    description: str
    tags: List[str] = []
    language: Optional[str] = None
    created_at: str
    updated_at: str
    files: List[FileMetadata] = []
    stats: dict = Field(default_factory=dict)