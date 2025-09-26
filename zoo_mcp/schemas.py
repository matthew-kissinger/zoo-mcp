from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class RateLimit(BaseModel):
    remaining: int
    reset: int


class RepoItem(BaseModel):
    full_name: str
    html_url: str
    default_branch: str
    license: Optional[str] = None
    stargazers_count: int
    pushed_at: str


class GHSearchReposInput(BaseModel):
    q: str
    sort: Optional[Literal["stars", "updated", "help-wanted-issues", "best-match"]] = "best-match"
    order: Optional[Literal["desc", "asc"]] = "desc"
    per_page: Optional[int] = Field(default=50, le=100)
    page: Optional[int] = 1
    time_windows: Optional[List[str]] = None


class GHSearchReposOutput(BaseModel):
    items: List[RepoItem]
    rate: RateLimit


class CodeItem(BaseModel):
    repository: str
    path: str
    html_url: str


class GHSearchCodeInput(BaseModel):
    q: str
    per_page: Optional[int] = Field(default=50, le=100)
    page: Optional[int] = 1


class GHSearchCodeOutput(BaseModel):
    items: List[CodeItem]
    rate: RateLimit


class ContentItem(BaseModel):
    name: str
    path: str
    download_url: Optional[str] = None
    size: Optional[int] = None
    content: Optional[str] = None
    saved_path: Optional[str] = None


class GHGetContentsInput(BaseModel):
    owner: str
    repo: str
    path: str
    ref: Optional[str] = None
    save_to: Optional[str] = None


class GHGetContentsOutput(BaseModel):
    type: Literal["file", "dir"]
    items: List[ContentItem]
    rate: RateLimit


class GHGetArchiveInput(BaseModel):
    owner: str
    repo: str
    ref: Optional[str] = None
    format: Optional[Literal["zipball", "tarball"]] = "zipball"
    save_to: Optional[str] = None


class GHGetArchiveOutput(BaseModel):
    archive_path: str
    bytes: int


class ReleaseItem(BaseModel):
    tag: str
    name: str
    body: str
    html_url: str


class GHReleasesInput(BaseModel):
    owner: str
    repo: str
    limit: Optional[int] = 5


class GHReleasesOutput(BaseModel):
    releases: List[ReleaseItem]
    rate: RateLimit


class CodeBlock(BaseModel):
    lang: Optional[str] = None
    text: str


class IssueWithCode(BaseModel):
    number: int
    title: str
    html_url: str
    code_blocks: List[CodeBlock]


class GHIssuesWithCodeInput(BaseModel):
    owner: str
    repo: str
    q: str
    limit: Optional[int] = 20


class GHIssuesWithCodeOutput(BaseModel):
    items: List[IssueWithCode]
    rate: RateLimit


class GrepHit(BaseModel):
    repo: str
    ref: str
    path: str
    snippet: str
    line_start: int
    line_end: int
    url: str


class GrepSearchInput(BaseModel):
    query: str
    language: Optional[str] = None
    path: Optional[str] = None
    limit: Optional[int] = 50


class GrepSearchOutput(BaseModel):
    hits: List[GrepHit]


class DependentRepo(BaseModel):
    repo: str
    url: str


class LibsIODependentsInput(BaseModel):
    package: str
    ecosystem: str
    limit: Optional[int] = 50


class LibsIODependentsOutput(BaseModel):
    dependents: List[DependentRepo]


class SOAnswer(BaseModel):
    question: str
    answer_url: str
    code_blocks: List[CodeBlock]


class SOAcceptedInput(BaseModel):
    q: str
    tags: Optional[List[str]] = None
    limit: Optional[int] = 10


class SOAcceptedOutput(BaseModel):
    answers: List[SOAnswer]