import pytest
from pathlib import Path
from zoo_mcp.guards import (
    validate_domain,
    validate_org_allowlist,
    safe_path_join,
    check_byte_budget,
    truncate_to_budget,
    parse_org_allowlist,
    SecurityError,
    ByteBudgetExceeded,
)


def test_validate_domain():
    validate_domain("https://github.com/owner/repo")
    validate_domain("https://gitlab.com/owner/repo")

    with pytest.raises(SecurityError):
        validate_domain("https://evil.com/malicious")


def test_validate_org_allowlist():
    allowlist = ["aws-samples", "GoogleCloudPlatform"]

    assert validate_org_allowlist("aws-samples", allowlist) is True
    assert validate_org_allowlist("AWS-SAMPLES", allowlist) is True
    assert validate_org_allowlist("random-org", allowlist) is False
    assert validate_org_allowlist("anything", None) is True


def test_safe_path_join(tmp_path):
    base = tmp_path / "workspace"
    base.mkdir()

    safe = safe_path_join(base, "subdir", "file.txt")
    assert str(safe).startswith(str(base))

    with pytest.raises(SecurityError):
        safe_path_join(base, "..", "..", "etc", "passwd")


def test_check_byte_budget():
    check_byte_budget("small text", 1000)

    with pytest.raises(ByteBudgetExceeded):
        check_byte_budget("x" * 10000, 100)


def test_truncate_to_budget():
    text = "a" * 1000
    truncated = truncate_to_budget(text, 100)
    assert len(truncated.encode("utf-8")) <= 150
    assert "truncated" in truncated

    small = "small"
    assert truncate_to_budget(small, 1000) == small


def test_parse_org_allowlist():
    assert parse_org_allowlist("aws,google,microsoft") == ["aws", "google", "microsoft"]
    assert parse_org_allowlist("  aws  ,  google  ") == ["aws", "google"]
    assert parse_org_allowlist("") is None
    assert parse_org_allowlist(None) is None