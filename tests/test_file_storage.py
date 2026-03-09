"""Unit tests for FileStorage class."""

import json
import tempfile
from pathlib import Path

import pytest

from qa_agent.models.base import Requirement, RequirementType
from qa_agent.storage import FileStorage


@pytest.fixture
def temp_storage_dir():
    """Create a temporary directory for storage tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def file_storage(temp_storage_dir):
    """Create a FileStorage instance with temporary directory."""
    return FileStorage(temp_storage_dir)


@pytest.fixture
def sample_requirements():
    """Create sample requirements for testing."""
    return [
        Requirement(
            type=RequirementType.FUNCTIONAL,
            content="User shall be able to login",
            source="requirements.md",
        ),
        Requirement(
            type=RequirementType.USER_STORY,
            content="As a user, I want to reset my password",
            source="user_stories.md",
        ),
        Requirement(
            type=RequirementType.API_ENDPOINT,
            content="POST /api/users - Create new user",
            source="api_spec.yaml",
        ),
    ]


class TestFileStorageSave:
    """Tests for FileStorage.save() method."""

    def test_save_requirements_success(self, file_storage, sample_requirements):
        """Test saving requirements successfully."""
        file_path = file_storage.save(sample_requirements, "test_requirements")

        assert file_path.exists()
        assert file_path.name == "test_requirements.json"
        assert file_path.parent == file_storage.storage_dir

    def test_save_creates_directory(self, temp_storage_dir, sample_requirements):
        """Test that save creates storage directory if it doesn't exist."""
        storage_dir = temp_storage_dir / "nested" / "directory"
        file_storage = FileStorage(storage_dir)

        assert not storage_dir.exists()

        file_path = file_storage.save(sample_requirements, "test")

        assert storage_dir.exists()
        assert file_path.exists()

    def test_save_adds_json_extension(self, file_storage, sample_requirements):
        """Test that .json extension is added if not present."""
        file_path = file_storage.save(sample_requirements, "test_file")

        assert file_path.name == "test_file.json"

    def test_save_preserves_json_extension(self, file_storage, sample_requirements):
        """Test that .json extension is not duplicated."""
        file_path = file_storage.save(sample_requirements, "test_file.json")

        assert file_path.name == "test_file.json"

    def test_save_empty_list_raises_error(self, file_storage):
        """Test that saving empty list raises ValueError."""
        with pytest.raises(ValueError, match="Cannot save empty requirements list"):
            file_storage.save([], "test")

    def test_save_empty_filename_raises_error(self, file_storage, sample_requirements):
        """Test that empty filename raises ValueError."""
        with pytest.raises(ValueError, match="Filename cannot be empty"):
            file_storage.save(sample_requirements, "")

    def test_save_whitespace_filename_raises_error(self, file_storage, sample_requirements):
        """Test that whitespace-only filename raises ValueError."""
        with pytest.raises(ValueError, match="Filename cannot be empty"):
            file_storage.save(sample_requirements, "   ")

    def test_save_json_format(self, file_storage, sample_requirements):
        """Test that saved JSON has correct format."""
        file_path = file_storage.save(sample_requirements, "test")

        with open(file_path, "r") as f:
            data = json.load(f)

        assert isinstance(data, list)
        assert len(data) == 3
        assert all("id" in item for item in data)
        assert all("type" in item for item in data)
        assert all("content" in item for item in data)
        assert all("source" in item for item in data)
        assert all("timestamp" in item for item in data)

    def test_save_preserves_requirement_data(self, file_storage, sample_requirements):
        """Test that saved data preserves requirement content."""
        file_path = file_storage.save(sample_requirements, "test")

        with open(file_path, "r") as f:
            data = json.load(f)

        assert data[0]["content"] == "User shall be able to login"
        assert data[0]["type"] == "functional"
        assert data[1]["content"] == "As a user, I want to reset my password"
        assert data[1]["type"] == "user_story"


class TestFileStorageLoad:
    """Tests for FileStorage.load() method."""

    def test_load_requirements_success(self, file_storage, sample_requirements):
        """Test loading requirements successfully."""
        file_storage.save(sample_requirements, "test")
        loaded = file_storage.load("test")

        assert len(loaded) == 3
        assert all(isinstance(req, Requirement) for req in loaded)

    def test_load_preserves_content(self, file_storage, sample_requirements):
        """Test that loaded requirements preserve content."""
        file_storage.save(sample_requirements, "test")
        loaded = file_storage.load("test")

        assert loaded[0].content == sample_requirements[0].content
        assert loaded[1].content == sample_requirements[1].content
        assert loaded[2].content == sample_requirements[2].content

    def test_load_preserves_type(self, file_storage, sample_requirements):
        """Test that loaded requirements preserve type."""
        file_storage.save(sample_requirements, "test")
        loaded = file_storage.load("test")

        assert loaded[0].type == RequirementType.FUNCTIONAL
        assert loaded[1].type == RequirementType.USER_STORY
        assert loaded[2].type == RequirementType.API_ENDPOINT

    def test_load_with_json_extension(self, file_storage, sample_requirements):
        """Test loading with .json extension."""
        file_storage.save(sample_requirements, "test")
        loaded = file_storage.load("test.json")

        assert len(loaded) == 3

    def test_load_without_json_extension(self, file_storage, sample_requirements):
        """Test loading without .json extension."""
        file_storage.save(sample_requirements, "test")
        loaded = file_storage.load("test")

        assert len(loaded) == 3

    def test_load_nonexistent_file_raises_error(self, file_storage):
        """Test that loading non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="Requirements file not found"):
            file_storage.load("nonexistent")

    def test_load_empty_filename_raises_error(self, file_storage):
        """Test that empty filename raises ValueError."""
        with pytest.raises(ValueError, match="Filename cannot be empty"):
            file_storage.load("")

    def test_load_invalid_json_raises_error(self, file_storage):
        """Test that invalid JSON raises ValueError."""
        # Create invalid JSON file
        file_path = file_storage.storage_dir / "invalid.json"
        file_storage.storage_dir.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w") as f:
            f.write("{invalid json")

        with pytest.raises(ValueError, match="Failed to parse JSON"):
            file_storage.load("invalid")

    def test_load_non_list_json_raises_error(self, file_storage):
        """Test that non-list JSON raises ValueError."""
        # Create JSON with object instead of array
        file_path = file_storage.storage_dir / "not_list.json"
        file_storage.storage_dir.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w") as f:
            json.dump({"key": "value"}, f)

        with pytest.raises(ValueError, match="Expected a JSON array"):
            file_storage.load("not_list")

    def test_load_invalid_requirement_data_raises_error(self, file_storage):
        """Test that invalid requirement data raises ValueError."""
        # Create JSON with invalid requirement structure
        file_path = file_storage.storage_dir / "invalid_req.json"
        file_storage.storage_dir.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w") as f:
            json.dump([{"invalid": "data"}], f)

        with pytest.raises(ValueError, match="Failed to deserialize requirements"):
            file_storage.load("invalid_req")


class TestFileStorageList:
    """Tests for FileStorage.list() method."""

    def test_list_empty_directory(self, file_storage):
        """Test listing files in empty directory."""
        files = file_storage.list()

        assert files == []

    def test_list_nonexistent_directory(self, temp_storage_dir):
        """Test listing files when directory doesn't exist."""
        storage_dir = temp_storage_dir / "nonexistent"
        file_storage = FileStorage(storage_dir)

        files = file_storage.list()

        assert files == []

    def test_list_all_files(self, file_storage, sample_requirements):
        """Test listing all JSON files."""
        file_storage.save(sample_requirements, "file1")
        file_storage.save(sample_requirements, "file2")
        file_storage.save(sample_requirements, "file3")

        files = file_storage.list()

        assert len(files) == 3
        assert all(f.suffix == ".json" for f in files)

    def test_list_with_pattern(self, file_storage, sample_requirements):
        """Test listing files with glob pattern."""
        file_storage.save(sample_requirements, "user_story_1")
        file_storage.save(sample_requirements, "user_story_2")
        file_storage.save(sample_requirements, "api_spec")

        files = file_storage.list("user_*")

        assert len(files) == 2
        assert all("user_story" in f.name for f in files)

    def test_list_sorted_by_modification_time(self, file_storage, sample_requirements):
        """Test that files are sorted by modification time (newest first)."""
        import time

        file_storage.save(sample_requirements, "old_file")
        time.sleep(0.01)
        file_storage.save(sample_requirements, "new_file")

        files = file_storage.list()

        assert len(files) == 2
        assert files[0].name == "new_file.json"
        assert files[1].name == "old_file.json"

    def test_list_returns_path_objects(self, file_storage, sample_requirements):
        """Test that list returns Path objects."""
        file_storage.save(sample_requirements, "test")

        files = file_storage.list()

        assert len(files) == 1
        assert isinstance(files[0], Path)


class TestFileStorageIntegration:
    """Integration tests for FileStorage."""

    def test_save_and_load_roundtrip(self, file_storage, sample_requirements):
        """Test that save and load preserve all data."""
        file_storage.save(sample_requirements, "roundtrip")
        loaded = file_storage.load("roundtrip")

        assert len(loaded) == len(sample_requirements)
        for original, loaded_req in zip(sample_requirements, loaded):
            assert loaded_req.content == original.content
            assert loaded_req.type == original.type
            assert loaded_req.source == original.source

    def test_multiple_files_independent(self, file_storage, sample_requirements):
        """Test that multiple files are stored independently."""
        req1 = [sample_requirements[0]]
        req2 = [sample_requirements[1]]

        file_storage.save(req1, "file1")
        file_storage.save(req2, "file2")

        loaded1 = file_storage.load("file1")
        loaded2 = file_storage.load("file2")

        assert len(loaded1) == 1
        assert len(loaded2) == 1
        assert loaded1[0].content != loaded2[0].content

    def test_overwrite_existing_file(self, file_storage, sample_requirements):
        """Test that saving to existing filename overwrites the file."""
        file_storage.save([sample_requirements[0]], "test")
        file_storage.save(sample_requirements, "test")

        loaded = file_storage.load("test")

        assert len(loaded) == 3
