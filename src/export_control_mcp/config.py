"""Configuration settings for Export Control MCP server."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All settings can be overridden via environment variables with the
    EXPORT_CONTROL_ prefix (e.g., EXPORT_CONTROL_MCP_TRANSPORT=sse).
    """

    model_config = SettingsConfigDict(
        env_prefix="EXPORT_CONTROL_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # MCP Transport Configuration
    mcp_transport: str = "stdio"
    mcp_host: str = "127.0.0.1"
    mcp_port: int = 8000

    # Embedding Model Configuration
    # Options: all-MiniLM-L6-v2 (fast, 384d), BAAI/bge-small-en-v1.5 (better quality)
    embedding_model: str = "all-MiniLM-L6-v2"

    # Storage Paths
    chroma_persist_dir: str = "./data/chroma"
    sanctions_db_path: str = "./data/sanctions.db"

    # Logging Configuration
    log_level: str = "INFO"
    audit_log_path: str = "./logs/audit.jsonl"

    @property
    def chroma_path(self) -> Path:
        """Return ChromaDB path as Path object."""
        return Path(self.chroma_persist_dir)

    @property
    def sanctions_db(self) -> Path:
        """Return sanctions database path as Path object."""
        return Path(self.sanctions_db_path)

    @property
    def audit_log(self) -> Path:
        """Return audit log path as Path object."""
        return Path(self.audit_log_path)


settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings
