"""File-based storage implementation for requirements and test artifacts."""

import json
from pathlib import Path
from typing import List, Optional

from qa_agent.core.exceptions import StorageError, ValidationError
from qa_agent.core.logging_config import get_logger, log_exception, log_operation_complete, log_operation_start
from qa_agent.models.base import Requirement

logger = get_logger(__name__)


class FileStorage:
    """File-based storage for requirements using JSON format."""

    def __init__(self, storage_dir: Path | str = "output/requirements"):
        """
        Initialize file storage.

        Args:
            storage_dir: Directory to store requirement files
        """
        self.storage_dir = Path(storage_dir)

    def save(self, requirements: List[Requirement], filename: str) -> Path:
        """
        Save requirements to a JSON file.

        Args:
            requirements: List of requirements to save
            filename: Name of the file (without extension)

        Returns:
            Path to the saved file

        Raises:
            StorageError: If file cannot be written
            ValidationError: If requirements list is empty or filename is invalid
        """
        log_operation_start(logger, "save_requirements", filename=filename, count=len(requirements))
        
        try:
            if not requirements:
                raise ValidationError(
                    "Cannot save empty requirements list",
                    field="requirements",
                    value="empty list"
                )

            if not filename or not filename.strip():
                raise ValidationError(
                    "Filename cannot be empty",
                    field="filename",
                    value=filename
                )

            # Sanitize filename
            filename = filename.strip()
            if not filename.endswith(".json"):
                filename = f"{filename}.json"

            # Ensure storage directory exists
            try:
                self.storage_dir.mkdir(parents=True, exist_ok=True)
                logger.debug(
                    f"Ensured storage directory exists: {self.storage_dir}",
                    extra={"extra_fields": {"storage_dir": str(self.storage_dir)}}
                )
            except PermissionError as e:
                raise StorageError(
                    f"Permission denied creating storage directory: {self.storage_dir}",
                    file_path=str(self.storage_dir),
                    operation="mkdir",
                    details={"error": "Insufficient permissions"}
                ) from e
            except Exception as e:
                raise StorageError(
                    f"Failed to create storage directory: {self.storage_dir}",
                    file_path=str(self.storage_dir),
                    operation="mkdir",
                    details={"error": str(e)}
                ) from e

            file_path = self.storage_dir / filename

            # Convert requirements to JSON-serializable format
            try:
                requirements_data = [req.model_dump(mode="json") for req in requirements]
            except Exception as e:
                raise StorageError(
                    "Failed to serialize requirements to JSON",
                    file_path=str(file_path),
                    operation="serialize",
                    details={"error": str(e), "requirements_count": len(requirements)}
                ) from e

            # Write to file
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(requirements_data, f, indent=2, ensure_ascii=False)
            except PermissionError as e:
                raise StorageError(
                    f"Permission denied writing to file: {file_path}",
                    file_path=str(file_path),
                    operation="write",
                    details={"error": "Insufficient permissions"}
                ) from e
            except OSError as e:
                raise StorageError(
                    f"Failed to write requirements to file: {file_path}",
                    file_path=str(file_path),
                    operation="write",
                    details={"error": str(e), "error_type": type(e).__name__}
                ) from e
            except Exception as e:
                raise StorageError(
                    f"Unexpected error writing to file: {file_path}",
                    file_path=str(file_path),
                    operation="write",
                    details={"error": str(e)}
                ) from e

            log_operation_complete(
                logger,
                "save_requirements",
                filename=filename,
                file_path=str(file_path),
                count=len(requirements)
            )
            
            logger.info(
                f"Successfully saved {len(requirements)} requirements to {file_path}",
                extra={"extra_fields": {"file_path": str(file_path), "count": len(requirements)}}
            )
            
            return file_path
            
        except (StorageError, ValidationError):
            # Re-raise known errors
            raise
        except Exception as e:
            # Wrap unexpected errors
            error = StorageError(
                f"Unexpected error saving requirements: {str(e)}",
                file_path=str(self.storage_dir / filename) if filename else None,
                operation="save",
                details={"original_error": str(e)}
            )
            log_exception(logger, error, "Failed to save requirements", filename=filename)
            raise error from e

    def load(self, filename: str) -> List[Requirement]:
        """
        Load requirements from a JSON file.

        Args:
            filename: Name of the file to load (with or without .json extension)

        Returns:
            List of loaded requirements

        Raises:
            FileNotFoundError: If the file doesn't exist
            StorageError: If file cannot be read or contains invalid data
            ValidationError: If filename is invalid
        """
        log_operation_start(logger, "load_requirements", filename=filename)
        
        try:
            if not filename or not filename.strip():
                raise ValidationError(
                    "Filename cannot be empty",
                    field="filename",
                    value=filename
                )

            filename = filename.strip()
            if not filename.endswith(".json"):
                filename = f"{filename}.json"

            file_path = self.storage_dir / filename

            if not file_path.exists():
                raise FileNotFoundError(
                    f"Requirements file not found: {file_path}\n"
                    f"Please ensure the file exists in the storage directory: {self.storage_dir}"
                )

            if not file_path.is_file():
                raise StorageError(
                    f"Path is not a file: {file_path}",
                    file_path=str(file_path),
                    operation="load",
                    details={"path_type": "directory" if file_path.is_dir() else "unknown"}
                )

            # Read file
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    requirements_data = json.load(f)
            except json.JSONDecodeError as e:
                raise StorageError(
                    f"Failed to parse JSON from file: {file_path}",
                    file_path=str(file_path),
                    operation="parse",
                    details={
                        "error": str(e),
                        "line": e.lineno if hasattr(e, "lineno") else None,
                        "column": e.colno if hasattr(e, "colno") else None,
                    }
                ) from e
            except UnicodeDecodeError as e:
                raise StorageError(
                    f"Failed to read file (encoding error): {file_path}",
                    file_path=str(file_path),
                    operation="read",
                    details={"error": "File is not valid UTF-8 encoded text"}
                ) from e
            except PermissionError as e:
                raise StorageError(
                    f"Permission denied reading file: {file_path}",
                    file_path=str(file_path),
                    operation="read",
                    details={"error": "Insufficient permissions"}
                ) from e
            except Exception as e:
                raise StorageError(
                    f"Failed to read requirements file: {file_path}",
                    file_path=str(file_path),
                    operation="read",
                    details={"error": str(e)}
                ) from e

            if not isinstance(requirements_data, list):
                raise StorageError(
                    f"Invalid requirements file format: {file_path}",
                    file_path=str(file_path),
                    operation="validate",
                    details={
                        "expected": "JSON array",
                        "actual": type(requirements_data).__name__
                    }
                )

            # Deserialize requirements
            try:
                requirements = [Requirement(**req_data) for req_data in requirements_data]
            except Exception as e:
                raise StorageError(
                    f"Failed to deserialize requirements from file: {file_path}",
                    file_path=str(file_path),
                    operation="deserialize",
                    details={"error": str(e), "records_count": len(requirements_data)}
                ) from e

            log_operation_complete(
                logger,
                "load_requirements",
                filename=filename,
                file_path=str(file_path),
                count=len(requirements)
            )
            
            logger.info(
                f"Successfully loaded {len(requirements)} requirements from {file_path}",
                extra={"extra_fields": {"file_path": str(file_path), "count": len(requirements)}}
            )
            
            return requirements
            
        except (FileNotFoundError, StorageError, ValidationError):
            # Re-raise known errors
            raise
        except Exception as e:
            # Wrap unexpected errors
            error = StorageError(
                f"Unexpected error loading requirements: {str(e)}",
                file_path=str(self.storage_dir / filename) if filename else None,
                operation="load",
                details={"original_error": str(e)}
            )
            log_exception(logger, error, "Failed to load requirements", filename=filename)
            raise error from e

    def list(self, pattern: Optional[str] = None) -> List[Path]:
        """
        List saved requirement files in the storage directory.

        Args:
            pattern: Optional glob pattern to filter files (e.g., "user_*")

        Returns:
            List of file paths matching the pattern

        Raises:
            OSError: If directory cannot be accessed
        """
        if not self.storage_dir.exists():
            return []

        try:
            if pattern:
                # Use glob pattern
                if not pattern.endswith(".json"):
                    pattern = f"{pattern}.json"
                files = list(self.storage_dir.glob(pattern))
            else:
                # List all JSON files
                files = list(self.storage_dir.glob("*.json"))

            # Sort by modification time (newest first)
            files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            return files
        except Exception as e:
            raise OSError(
                f"Failed to list files in storage directory: {self.storage_dir}\n"
                f"Error: {str(e)}"
            ) from e
