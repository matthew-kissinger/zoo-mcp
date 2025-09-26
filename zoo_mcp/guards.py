import os
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse


class SecurityError(Exception):
    pass


class ByteBudgetExceeded(Exception):
    pass


ALLOWED_DOMAINS = {"github.com", "gitlab.com"}


def validate_domain(url: str) -> None:
    parsed = urlparse(url)
    if parsed.netloc not in ALLOWED_DOMAINS:
        raise SecurityError(f"Domain {parsed.netloc} not in allowlist: {ALLOWED_DOMAINS}")


def validate_org_allowlist(org: str, allowlist: Optional[list[str]]) -> bool:
    if not allowlist:
        return True
    return org.lower() in [o.lower() for o in allowlist]


def safe_path_join(base: Path, *parts: str) -> Path:
    base = base.resolve()
    target = (base / Path(*parts)).resolve()

    if not str(target).startswith(str(base)):
        raise SecurityError(f"Path traversal detected: {target} is outside {base}")

    return target


def ensure_workspace(workspace_path: str) -> Path:
    workspace = Path(workspace_path).resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    return workspace


def check_byte_budget(data: str, max_bytes: int) -> None:
    size = len(data.encode("utf-8"))
    if size > max_bytes:
        raise ByteBudgetExceeded(
            f"Response size {size} bytes exceeds budget of {max_bytes} bytes"
        )


def truncate_to_budget(data: str, max_bytes: int) -> str:
    encoded = data.encode("utf-8")
    if len(encoded) <= max_bytes:
        return data

    truncated = encoded[:max_bytes].decode("utf-8", errors="ignore")
    return truncated + "\n[... truncated to fit byte budget]"


def parse_org_allowlist(env_var: Optional[str]) -> Optional[list[str]]:
    if not env_var:
        return None
    return [org.strip() for org in env_var.split(",") if org.strip()]