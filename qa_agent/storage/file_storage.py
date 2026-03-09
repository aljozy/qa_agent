"""File-based storage implementation for requirements and test artifacts."""

import json
from pathlib import Path
from typing import List, Optional

from qa_agent.models.base import Requirement


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
            OSError: If file cannot be written
            ValueError: If requirements list is empty or filename is invalid
        """
        if not requirements:
            raise ValueError("Cannot save empty requirements list")

        if not filename or not filename.strip():
            raise ValueError("Filename cannot be empty")

        # Sanitize filename
        filename = filename.strip()
        if not filename.endswith(".json"):
            filename = f"{filename}.json"

        # Ensure storage directory exists
        try:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise OSError(
                f"Failed to create storage directory: {self.storage_dir}\n"
                f"Error: {str(e)}"
            ) from e

        file_path = self.storage_dir / filename

        # Convert requirements to JSON-serializable format
        try:
            requirements_data = [req.model_dump(mode="json") for req in requirements]
        except Exception as e:
            raise ValueError(
                f"Failed to serialize requirements to JSON\n"
                f"Error: {str(e)}"
            ) from e

        # Write to file
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(requirements_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise OSError(
                f"Failed to write requirements to file: {file_path}\n"
                f"Error: {str(e)}"
            ) from e

        return file_path

    def load(self, filename: str) -> List[Requirement]:
        """
        Load requirements from a JSON file.

        Args:
            filename: Name of the file to load (with or without .json extension)

        Returns:
            List of loaded requirements

        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file contains invalid data
            OSError: If file cannot be read
        """
        if not filename or not filename.strip():
            raise ValueError("Filename cannot be empty")

        filename = filename.strip()
        if not filename.endswith(".json"):
            filename = f"{filename}.json"

        file_path = self.storage_dir / filename

        if not file_path.exists():
            raise FileNotFoundError(
                f"Requirements file not found: {file_path}\n"
                f"Please ensure the file exists in the storage directory."
            )

        if not file_path.is_file():
            raise ValueError(
                f"Path is not a file: {file_path}\n"
                f"Please provide a valid requirements file."
            )

        # Read file
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                requirements_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Failed to parse JSON from file: {file_path}\n"
                f"Error: {str(e)}\n"
                f"Please ensure the file contains valid JSON."
            ) from e
        except Exception as e:
            raise OSError(
                f"Failed to read requirements file: {file_path}\n"
                f"Error: {str(e)}"
            ) from e

        if not isinstance(requirements_data, list):
            raise ValueError(
                f"Invalid requirements file format: {file_path}\n"
                f"Expected a JSON array, got {type(requirements_data)}"
            )

        # Deserialize requirements
        try:
            requirements = [Requirement(**req_data) for req_data in requirements_data]
        except Exception as e:
            raise ValueError(
                f"Failed to deserialize requirements from file: {file_path}\n"
                f"Error: {str(e)}\n"
                f"Please ensure the file contains valid requirement data."
            ) from e

        return requirements

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
