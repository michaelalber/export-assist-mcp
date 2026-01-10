"""Custom exception hierarchy for Export Control MCP."""


class ExportControlError(Exception):
    """Base exception for all Export Control MCP errors."""

    pass


class RegulationNotFoundError(ExportControlError):
    """Raised when a requested regulation section does not exist."""

    def __init__(self, regulation_id: str, regulation_type: str | None = None):
        self.regulation_id = regulation_id
        self.regulation_type = regulation_type
        if regulation_type:
            message = f"Regulation '{regulation_id}' not found in {regulation_type.upper()}"
        else:
            message = f"Regulation '{regulation_id}' not found"
        super().__init__(message)


class ECCNNotFoundError(ExportControlError):
    """Raised when a requested ECCN does not exist."""

    def __init__(self, eccn: str):
        self.eccn = eccn
        super().__init__(f"ECCN '{eccn}' not found in Commerce Control List")


class USMLCategoryNotFoundError(ExportControlError):
    """Raised when a requested USML category does not exist."""

    def __init__(self, category: str):
        self.category = category
        super().__init__(f"USML Category '{category}' not found")


class VectorStoreError(ExportControlError):
    """Raised for ChromaDB operation failures."""

    pass


class EmbeddingError(ExportControlError):
    """Raised when embedding generation fails."""

    pass


class AuditLogError(ExportControlError):
    """Raised when audit logging fails."""

    pass


class SanctionsQueryError(ExportControlError):
    """Raised when a sanctions database query fails."""

    def __init__(self, message: str, list_type: str | None = None):
        self.list_type = list_type
        if list_type:
            full_message = f"Error querying {list_type}: {message}"
        else:
            full_message = f"Sanctions query error: {message}"
        super().__init__(full_message)


class IngestionError(ExportControlError):
    """Raised when data ingestion fails."""

    def __init__(self, source: str, message: str):
        self.source = source
        super().__init__(f"Failed to ingest '{source}': {message}")


class DataNotFoundError(ExportControlError):
    """Raised when required data files are missing."""

    def __init__(self, path: str):
        self.path = path
        super().__init__(f"Required data not found at '{path}'. Run ingestion first.")
