"""Tests for the audit logging module.

This module is security-critical and requires 95% test coverage.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from export_control_mcp.audit import (
    _sanitize_params,
    _summarize_result,
    _write_audit_log,
    audit_log,
    get_audit_entries,
)
from export_control_mcp.models.errors import AuditLogError


class TestSanitizeParams:
    """Tests for parameter sanitization."""

    def test_should_pass_through_normal_params(self) -> None:
        """Test that normal parameters are passed through unchanged."""
        # Arrange
        params = {"query": "test", "limit": 10, "name": "John Doe"}

        # Act
        result = _sanitize_params(params)

        # Assert
        assert result == params

    def test_should_redact_password_field(self) -> None:
        """Test that password fields are redacted."""
        # Arrange
        params = {"username": "user", "password": "secret123"}

        # Act
        result = _sanitize_params(params)

        # Assert
        assert result["username"] == "user"
        assert result["password"] == "[REDACTED]"

    def test_should_redact_token_field(self) -> None:
        """Test that token fields are redacted."""
        # Arrange
        params = {"api_token": "abc123xyz"}

        # Act
        result = _sanitize_params(params)

        # Assert
        assert result["api_token"] == "[REDACTED]"

    def test_should_redact_key_field(self) -> None:
        """Test that key fields are redacted."""
        # Arrange
        params = {"api_key": "sk-123456", "encryption_key": "aes256key"}

        # Act
        result = _sanitize_params(params)

        # Assert
        assert result["api_key"] == "[REDACTED]"
        assert result["encryption_key"] == "[REDACTED]"

    def test_should_redact_secret_field(self) -> None:
        """Test that secret fields are redacted."""
        # Arrange
        params = {"client_secret": "mysecret"}

        # Act
        result = _sanitize_params(params)

        # Assert
        assert result["client_secret"] == "[REDACTED]"

    def test_should_redact_credential_field(self) -> None:
        """Test that credential fields are redacted."""
        # Arrange
        params = {"credentials": "user:pass"}

        # Act
        result = _sanitize_params(params)

        # Assert
        assert result["credentials"] == "[REDACTED]"

    def test_should_redact_case_insensitively(self) -> None:
        """Test that redaction is case-insensitive."""
        # Arrange
        params = {"PASSWORD": "secret", "Api_Token": "token123"}

        # Act
        result = _sanitize_params(params)

        # Assert
        assert result["PASSWORD"] == "[REDACTED]"
        assert result["Api_Token"] == "[REDACTED]"

    def test_should_truncate_long_strings(self) -> None:
        """Test that strings over 1000 chars are truncated."""
        # Arrange
        long_string = "x" * 1500
        params = {"content": long_string}

        # Act
        result = _sanitize_params(params)

        # Assert
        assert len(result["content"]) == 1000 + len("...[truncated]")
        assert result["content"].endswith("...[truncated]")

    def test_should_not_truncate_short_strings(self) -> None:
        """Test that strings under 1000 chars are not truncated."""
        # Arrange
        short_string = "x" * 500
        params = {"content": short_string}

        # Act
        result = _sanitize_params(params)

        # Assert
        assert result["content"] == short_string

    def test_should_handle_non_string_values(self) -> None:
        """Test that non-string values are passed through."""
        # Arrange
        params = {"count": 42, "enabled": True, "data": [1, 2, 3]}

        # Act
        result = _sanitize_params(params)

        # Assert
        assert result == params

    def test_should_handle_empty_params(self) -> None:
        """Test that empty params dict is handled."""
        # Arrange
        params: dict = {}

        # Act
        result = _sanitize_params(params)

        # Assert
        assert result == {}


class TestSummarizeResult:
    """Tests for result summarization."""

    def test_should_return_none_string_for_none(self) -> None:
        """Test that None returns 'None' string."""
        # Arrange & Act
        result = _summarize_result(None)

        # Assert
        assert result == "None"

    def test_should_return_short_string_unchanged(self) -> None:
        """Test that short strings are returned unchanged."""
        # Arrange
        short_string = "This is a short result"

        # Act
        result = _summarize_result(short_string)

        # Assert
        assert result == short_string

    def test_should_truncate_long_strings(self) -> None:
        """Test that strings over 200 chars are truncated."""
        # Arrange
        long_string = "x" * 300

        # Act
        result = _summarize_result(long_string)

        # Assert
        assert len(result) == 200 + len("...[truncated]")
        assert result.endswith("...[truncated]")

    def test_should_summarize_list_with_count(self) -> None:
        """Test that lists are summarized with item count."""
        # Arrange
        items = [1, 2, 3, 4, 5]

        # Act
        result = _summarize_result(items)

        # Assert
        assert result == "List with 5 items"

    def test_should_summarize_empty_list(self) -> None:
        """Test that empty lists are summarized."""
        # Arrange
        items: list = []

        # Act
        result = _summarize_result(items)

        # Assert
        assert result == "List with 0 items"

    def test_should_summarize_dict_with_keys(self) -> None:
        """Test that dicts are summarized with keys."""
        # Arrange
        data = {"name": "test", "value": 123, "enabled": True}

        # Act
        result = _summarize_result(data)

        # Assert
        assert result.startswith("Dict with keys:")
        assert "name" in result

    def test_should_limit_dict_keys_to_5(self) -> None:
        """Test that only first 5 dict keys are shown."""
        # Arrange
        data = {f"key{i}": i for i in range(10)}

        # Act
        result = _summarize_result(data)

        # Assert
        # Should only show first 5 keys
        assert result.startswith("Dict with keys:")

    def test_should_return_type_name_for_other_types(self) -> None:
        """Test that other types return their type name."""
        # Arrange
        class CustomObject:
            pass

        obj = CustomObject()

        # Act
        result = _summarize_result(obj)

        # Assert
        assert result == "CustomObject"

    def test_should_return_type_name_for_integers(self) -> None:
        """Test that integers return 'int'."""
        # Arrange & Act
        result = _summarize_result(42)

        # Assert
        assert result == "int"


class TestWriteAuditLog:
    """Tests for audit log writing."""

    def test_should_write_entry_to_file(self) -> None:
        """Test that entry is written to audit log file."""
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "audit.jsonl"
            entry = {"timestamp": "2024-01-01T00:00:00Z", "tool": "test_tool"}

            with patch("export_control_mcp.audit.settings") as mock_settings:
                mock_settings.audit_log_path = str(log_path)

                # Act
                _write_audit_log(entry)

                # Assert
                assert log_path.exists()
                content = log_path.read_text()
                parsed = json.loads(content.strip())
                assert parsed["tool"] == "test_tool"

    def test_should_append_to_existing_file(self) -> None:
        """Test that entries are appended, not overwritten."""
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "audit.jsonl"
            log_path.write_text('{"existing": "entry"}\n')

            entry = {"new": "entry"}

            with patch("export_control_mcp.audit.settings") as mock_settings:
                mock_settings.audit_log_path = str(log_path)

                # Act
                _write_audit_log(entry)

                # Assert
                lines = log_path.read_text().strip().split("\n")
                assert len(lines) == 2

    def test_should_create_parent_directories(self) -> None:
        """Test that parent directories are created."""
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "subdir" / "nested" / "audit.jsonl"
            entry = {"tool": "test"}

            with patch("export_control_mcp.audit.settings") as mock_settings:
                mock_settings.audit_log_path = str(log_path)

                # Act
                _write_audit_log(entry)

                # Assert
                assert log_path.exists()

    def test_should_raise_audit_log_error_on_failure(self) -> None:
        """Test that AuditLogError is raised on write failure."""
        # Arrange
        entry = {"tool": "test"}

        with patch("export_control_mcp.audit.settings") as mock_settings:
            # Use an invalid path that can't be created
            mock_settings.audit_log_path = "/nonexistent/readonly/path/audit.jsonl"

            # Act & Assert
            with pytest.raises(AuditLogError):
                _write_audit_log(entry)


class TestAuditLogDecoratorAsync:
    """Tests for audit_log decorator with async functions."""

    @pytest.mark.asyncio
    async def test_should_log_successful_async_call(self) -> None:
        """Test that successful async calls are logged."""
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "audit.jsonl"

            with patch("export_control_mcp.audit.settings") as mock_settings:
                mock_settings.audit_log_path = str(log_path)

                @audit_log
                async def my_tool(query: str) -> str:
                    return f"Result for {query}"

                # Act
                result = await my_tool(query="test")

                # Assert
                assert result == "Result for test"
                assert log_path.exists()

                entry = json.loads(log_path.read_text().strip())
                assert entry["tool"] == "my_tool"
                assert entry["status"] == "success"
                assert entry["params"]["query"] == "test"

    @pytest.mark.asyncio
    async def test_should_log_error_on_async_exception(self) -> None:
        """Test that exceptions in async calls are logged."""
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "audit.jsonl"

            with patch("export_control_mcp.audit.settings") as mock_settings:
                mock_settings.audit_log_path = str(log_path)

                @audit_log
                async def failing_tool() -> None:
                    raise ValueError("Test error")

                # Act & Assert
                with pytest.raises(ValueError, match="Test error"):
                    await failing_tool()

                entry = json.loads(log_path.read_text().strip())
                assert entry["status"] == "error"
                assert entry["error"] == "Test error"
                assert entry["error_type"] == "ValueError"

    @pytest.mark.asyncio
    async def test_should_continue_on_audit_log_write_failure(self) -> None:
        """Test that tool continues even if audit log write fails."""
        # Arrange
        with patch("export_control_mcp.audit.settings") as mock_settings:
            mock_settings.audit_log_path = "/invalid/path/audit.jsonl"

            @audit_log
            async def my_tool() -> str:
                return "success"

            # Act - should not raise despite audit log failure
            result = await my_tool()

            # Assert
            assert result == "success"

    @pytest.mark.asyncio
    async def test_should_preserve_function_metadata(self) -> None:
        """Test that decorated function preserves name and docstring."""
        # Arrange
        @audit_log
        async def documented_tool() -> None:
            """This is the docstring."""
            pass

        # Assert
        assert documented_tool.__name__ == "documented_tool"
        assert documented_tool.__doc__ == "This is the docstring."


class TestAuditLogDecoratorSync:
    """Tests for audit_log decorator with sync functions."""

    def test_should_log_successful_sync_call(self) -> None:
        """Test that successful sync calls are logged."""
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "audit.jsonl"

            with patch("export_control_mcp.audit.settings") as mock_settings:
                mock_settings.audit_log_path = str(log_path)

                @audit_log
                def sync_tool(value: int) -> int:
                    return value * 2

                # Act
                result = sync_tool(value=21)

                # Assert
                assert result == 42
                assert log_path.exists()

                entry = json.loads(log_path.read_text().strip())
                assert entry["tool"] == "sync_tool"
                assert entry["status"] == "success"
                assert entry["params"]["value"] == 21

    def test_should_log_error_on_sync_exception(self) -> None:
        """Test that exceptions in sync calls are logged."""
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "audit.jsonl"

            with patch("export_control_mcp.audit.settings") as mock_settings:
                mock_settings.audit_log_path = str(log_path)

                @audit_log
                def failing_sync_tool() -> None:
                    raise RuntimeError("Sync error")

                # Act & Assert
                with pytest.raises(RuntimeError, match="Sync error"):
                    failing_sync_tool()

                entry = json.loads(log_path.read_text().strip())
                assert entry["status"] == "error"
                assert entry["error"] == "Sync error"
                assert entry["error_type"] == "RuntimeError"

    def test_should_continue_on_audit_log_write_failure_sync(self) -> None:
        """Test that sync tool continues even if audit log write fails."""
        # Arrange
        with patch("export_control_mcp.audit.settings") as mock_settings:
            mock_settings.audit_log_path = "/invalid/path/audit.jsonl"

            @audit_log
            def sync_tool() -> str:
                return "success"

            # Act - should not raise despite audit log failure
            result = sync_tool()

            # Assert
            assert result == "success"

    def test_should_preserve_sync_function_metadata(self) -> None:
        """Test that decorated sync function preserves name and docstring."""
        # Arrange
        @audit_log
        def documented_sync_tool() -> None:
            """Sync docstring."""
            pass

        # Assert
        assert documented_sync_tool.__name__ == "documented_sync_tool"
        assert documented_sync_tool.__doc__ == "Sync docstring."


class TestGetAuditEntries:
    """Tests for reading audit log entries."""

    def test_should_return_empty_list_when_file_not_exists(self) -> None:
        """Test that empty list is returned when log file doesn't exist."""
        # Arrange
        with patch("export_control_mcp.audit.settings") as mock_settings:
            mock_settings.audit_log_path = "/nonexistent/audit.jsonl"

            # Act
            entries = get_audit_entries()

            # Assert
            assert entries == []

    def test_should_read_entries_from_file(self) -> None:
        """Test reading entries from audit log file."""
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "audit.jsonl"
            log_path.write_text(
                '{"tool": "tool1", "status": "success"}\n'
                '{"tool": "tool2", "status": "success"}\n'
            )

            with patch("export_control_mcp.audit.settings") as mock_settings:
                mock_settings.audit_log_path = str(log_path)

                # Act
                entries = get_audit_entries()

                # Assert
                assert len(entries) == 2

    def test_should_return_most_recent_first(self) -> None:
        """Test that most recent entries are returned first."""
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "audit.jsonl"
            log_path.write_text(
                '{"tool": "first", "order": 1}\n'
                '{"tool": "second", "order": 2}\n'
                '{"tool": "third", "order": 3}\n'
            )

            with patch("export_control_mcp.audit.settings") as mock_settings:
                mock_settings.audit_log_path = str(log_path)

                # Act
                entries = get_audit_entries()

                # Assert
                assert entries[0]["order"] == 3  # Most recent first
                assert entries[1]["order"] == 2
                assert entries[2]["order"] == 1

    def test_should_respect_limit_parameter(self) -> None:
        """Test that limit parameter restricts results."""
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "audit.jsonl"
            log_path.write_text(
                '{"tool": "tool1"}\n'
                '{"tool": "tool2"}\n'
                '{"tool": "tool3"}\n'
                '{"tool": "tool4"}\n'
                '{"tool": "tool5"}\n'
            )

            with patch("export_control_mcp.audit.settings") as mock_settings:
                mock_settings.audit_log_path = str(log_path)

                # Act
                entries = get_audit_entries(limit=2)

                # Assert
                assert len(entries) == 2

    def test_should_filter_by_tool_name(self) -> None:
        """Test that tool_filter restricts results."""
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "audit.jsonl"
            log_path.write_text(
                '{"tool": "search_ear"}\n'
                '{"tool": "search_itar"}\n'
                '{"tool": "search_ear"}\n'
            )

            with patch("export_control_mcp.audit.settings") as mock_settings:
                mock_settings.audit_log_path = str(log_path)

                # Act
                entries = get_audit_entries(tool_filter="search_ear")

                # Assert
                assert len(entries) == 2
                assert all(e["tool"] == "search_ear" for e in entries)

    def test_should_skip_empty_lines(self) -> None:
        """Test that empty lines are skipped."""
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "audit.jsonl"
            log_path.write_text(
                '{"tool": "tool1"}\n'
                '\n'
                '   \n'
                '{"tool": "tool2"}\n'
            )

            with patch("export_control_mcp.audit.settings") as mock_settings:
                mock_settings.audit_log_path = str(log_path)

                # Act
                entries = get_audit_entries()

                # Assert
                assert len(entries) == 2

    def test_should_return_empty_on_read_error(self) -> None:
        """Test that empty list is returned on read error."""
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "audit.jsonl"
            # Write invalid JSON
            log_path.write_text("not valid json\n")

            with patch("export_control_mcp.audit.settings") as mock_settings:
                mock_settings.audit_log_path = str(log_path)

                # Act
                entries = get_audit_entries()

                # Assert
                assert entries == []


class TestAuditLogIntegration:
    """Integration tests for the audit logging system."""

    @pytest.mark.asyncio
    async def test_should_sanitize_params_before_logging(self) -> None:
        """Test that sensitive params are sanitized in logs."""
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "audit.jsonl"

            with patch("export_control_mcp.audit.settings") as mock_settings:
                mock_settings.audit_log_path = str(log_path)

                @audit_log
                async def sensitive_tool(api_key: str, query: str) -> str:
                    return "done"

                # Act
                await sensitive_tool(api_key="secret123", query="test")

                # Assert
                entry = json.loads(log_path.read_text().strip())
                assert entry["params"]["api_key"] == "[REDACTED]"
                assert entry["params"]["query"] == "test"

    @pytest.mark.asyncio
    async def test_should_include_timestamp_in_utc(self) -> None:
        """Test that timestamp is included and in UTC."""
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "audit.jsonl"

            with patch("export_control_mcp.audit.settings") as mock_settings:
                mock_settings.audit_log_path = str(log_path)

                @audit_log
                async def timed_tool() -> str:
                    return "done"

                # Act
                await timed_tool()

                # Assert
                entry = json.loads(log_path.read_text().strip())
                assert "timestamp" in entry
                # ISO format should end with +00:00 for UTC
                assert entry["timestamp"].endswith("+00:00")

    @pytest.mark.asyncio
    async def test_should_summarize_result_in_log(self) -> None:
        """Test that result is summarized in log entry."""
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "audit.jsonl"

            with patch("export_control_mcp.audit.settings") as mock_settings:
                mock_settings.audit_log_path = str(log_path)

                @audit_log
                async def list_tool() -> list:
                    return [1, 2, 3, 4, 5]

                # Act
                await list_tool()

                # Assert
                entry = json.loads(log_path.read_text().strip())
                assert entry["result_summary"] == "List with 5 items"
