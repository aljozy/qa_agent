"""Custom exception classes for the QA Agent system."""


class QAAgentError(Exception):
    """Base exception for all QA Agent errors."""

    def __init__(self, message: str, details: dict = None):
        """
        Initialize QA Agent error.
        
        Args:
            message: Error message
            details: Optional dictionary with additional error details
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def to_dict(self) -> dict:
        """Convert exception to dictionary format for logging."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
        }


class ParsingError(QAAgentError):
    """Exception raised when parsing requirements fails."""

    def __init__(self, message: str, source: str = None, line_number: int = None, details: dict = None):
        """
        Initialize parsing error.
        
        Args:
            message: Error message
            source: Source file or document being parsed
            line_number: Line number where error occurred (if applicable)
            details: Additional error details
        """
        error_details = details or {}
        if source:
            error_details["source"] = source
        if line_number:
            error_details["line_number"] = line_number
        
        super().__init__(message, error_details)
        self.source = source
        self.line_number = line_number


class ConfigurationError(QAAgentError):
    """Exception raised when configuration is invalid."""

    def __init__(self, message: str, config_file: str = None, field: str = None, details: dict = None):
        """
        Initialize configuration error.
        
        Args:
            message: Error message
            config_file: Configuration file path
            field: Configuration field that caused the error
            details: Additional error details
        """
        error_details = details or {}
        if config_file:
            error_details["config_file"] = config_file
        if field:
            error_details["field"] = field
        
        super().__init__(message, error_details)
        self.config_file = config_file
        self.field = field


class StorageError(QAAgentError):
    """Exception raised when storage operations fail."""

    def __init__(self, message: str, file_path: str = None, operation: str = None, details: dict = None):
        """
        Initialize storage error.
        
        Args:
            message: Error message
            file_path: File path involved in the operation
            operation: Operation that failed (read, write, delete, etc.)
            details: Additional error details
        """
        error_details = details or {}
        if file_path:
            error_details["file_path"] = file_path
        if operation:
            error_details["operation"] = operation
        
        super().__init__(message, error_details)
        self.file_path = file_path
        self.operation = operation


class GenerationError(QAAgentError):
    """Exception raised when test generation fails."""

    def __init__(self, message: str, requirement_id: str = None, provider: str = None, details: dict = None):
        """
        Initialize generation error.
        
        Args:
            message: Error message
            requirement_id: ID of requirement being processed
            provider: AI provider being used
            details: Additional error details
        """
        error_details = details or {}
        if requirement_id:
            error_details["requirement_id"] = requirement_id
        if provider:
            error_details["provider"] = provider
        
        super().__init__(message, error_details)
        self.requirement_id = requirement_id
        self.provider = provider


class LLMError(GenerationError):
    """Exception raised for LLM-related errors."""

    def __init__(self, message: str, provider: str = None, model: str = None, details: dict = None):
        """
        Initialize LLM error.
        
        Args:
            message: Error message
            provider: AI provider (kiro, openai, etc.)
            model: Model name
            details: Additional error details
        """
        error_details = details or {}
        if model:
            error_details["model"] = model
        
        super().__init__(message, provider=provider, details=error_details)
        self.model = model


class RateLimitError(LLMError):
    """Exception raised when rate limit is exceeded."""

    def __init__(self, message: str, provider: str = None, retry_after: int = None, details: dict = None):
        """
        Initialize rate limit error.
        
        Args:
            message: Error message
            provider: AI provider
            retry_after: Seconds to wait before retrying
            details: Additional error details
        """
        error_details = details or {}
        if retry_after:
            error_details["retry_after"] = retry_after
        
        super().__init__(message, provider=provider, details=error_details)
        self.retry_after = retry_after


class APIError(LLMError):
    """Exception raised for API-related errors."""

    def __init__(self, message: str, provider: str = None, status_code: int = None, details: dict = None):
        """
        Initialize API error.
        
        Args:
            message: Error message
            provider: AI provider
            status_code: HTTP status code (if applicable)
            details: Additional error details
        """
        error_details = details or {}
        if status_code:
            error_details["status_code"] = status_code
        
        super().__init__(message, provider=provider, details=error_details)
        self.status_code = status_code


class ValidationError(QAAgentError):
    """Exception raised when validation fails."""

    def __init__(self, message: str, field: str = None, value: any = None, details: dict = None):
        """
        Initialize validation error.
        
        Args:
            message: Error message
            field: Field that failed validation
            value: Value that failed validation
            details: Additional error details
        """
        error_details = details or {}
        if field:
            error_details["field"] = field
        if value is not None:
            error_details["value"] = str(value)
        
        super().__init__(message, error_details)
        self.field = field
        self.value = value


class RTMError(QAAgentError):
    """Exception raised when RTM generation fails."""

    def __init__(self, message: str, operation: str = None, details: dict = None):
        """
        Initialize RTM error.
        
        Args:
            message: Error message
            operation: Operation that failed (generate, export, etc.)
            details: Additional error details
        """
        error_details = details or {}
        if operation:
            error_details["operation"] = operation
        
        super().__init__(message, error_details)
        self.operation = operation
