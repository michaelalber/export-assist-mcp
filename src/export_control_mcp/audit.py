"""Audit logging for export control MCP tools.

Provides a decorator and utilities for logging all tool invocations
to a JSONL file for compliance and audit purposes.
"""

import json
import logging
from collections.abc import Callable
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path
from typing import Any, TypeVar

from export_control_mcp.config import settings
from export_control_mcp.models.errors import AuditLogError

logger = logging.getLogger(__name__)

# Type variable for decorated functions
F = TypeVar("F", bound=Callable[..., Any])


def _sanitize_params(params: dict[str, Any]) -> dict[str, Any]:
    """
    Sanitize parameters for logging.

    Removes or masks potentially sensitive information.
    """
    sanitized = {}
    sensitive_keys = {"password", "token", "key", "secret", "credential"}

    for key, value in params.items():
        key_lower = key.lower()
        if any(sensitive in key_lower for sensitive in sensitive_keys):
            sanitized[key] = "[REDACTED]"
        elif isinstance(value, str) and len(value) > 1000:
            sanitized[key] = value[:1000] + "...[truncated]"
        else:
            sanitized[key] = value

    return sanitized


def _summarize_result(result: Any) -> str:
    """Create a brief summary of the tool result."""
    if result is None:
        return "None"

    if isinstance(result, str):
        if len(result) > 200:
            return result[:200] + "...[truncated]"
        return result

    if isinstance(result, list):
        return f"List with {len(result)} items"

    if isinstance(result, dict):
        return f"Dict with keys: {list(result.keys())[:5]}"

    return str(type(result).__name__)


def _write_audit_log(entry: dict[str, Any]) -> None:
    """Write an entry to the audit log file."""
    log_path = Path(settings.audit_log_path)

    try:
        # Ensure directory exists
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Append to JSONL file
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, default=str) + "\n")

    except Exception as e:
        # Log error but don't crash the tool
        logger.error(f"Failed to write audit log: {e}")
        raise AuditLogError(f"Failed to write audit log: {e}") from e


def audit_log(func: F) -> F:
    """
    Decorator to log tool invocations for audit purposes.

    Logs timestamp, tool name, parameters, and result summary
    to a JSONL audit file.

    Usage:
        @mcp.tool()
        @audit_log
        async def my_tool(query: str) -> list[dict]:
            ...
    """

    @wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tool": func.__name__,
            "params": _sanitize_params(kwargs),
        }

        try:
            result = await func(*args, **kwargs)
            entry["status"] = "success"
            entry["result_summary"] = _summarize_result(result)
            return result

        except Exception as e:
            entry["status"] = "error"
            entry["error"] = str(e)
            entry["error_type"] = type(e).__name__
            raise

        finally:
            try:
                _write_audit_log(entry)
            except AuditLogError:
                # Already logged, just continue
                pass

    @wraps(func)
    def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tool": func.__name__,
            "params": _sanitize_params(kwargs),
        }

        try:
            result = func(*args, **kwargs)
            entry["status"] = "success"
            entry["result_summary"] = _summarize_result(result)
            return result

        except Exception as e:
            entry["status"] = "error"
            entry["error"] = str(e)
            entry["error_type"] = type(e).__name__
            raise

        finally:
            try:
                _write_audit_log(entry)
            except AuditLogError:
                pass

    # Return appropriate wrapper based on function type
    import asyncio

    if asyncio.iscoroutinefunction(func):
        return async_wrapper  # type: ignore[return-value]
    return sync_wrapper  # type: ignore[return-value]


def get_audit_entries(
    limit: int = 100,
    tool_filter: str | None = None,
) -> list[dict[str, Any]]:
    """
    Read recent audit log entries.

    Args:
        limit: Maximum number of entries to return.
        tool_filter: Optional tool name to filter by.

    Returns:
        List of audit entries, most recent first.
    """
    log_path = Path(settings.audit_log_path)

    if not log_path.exists():
        return []

    entries = []
    try:
        with open(log_path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line)
                    if tool_filter is None or entry.get("tool") == tool_filter:
                        entries.append(entry)
    except Exception as e:
        logger.error(f"Failed to read audit log: {e}")
        return []

    # Return most recent entries
    return entries[-limit:][::-1]
