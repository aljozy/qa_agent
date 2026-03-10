"""Tests for OpenAPI/Swagger specification parser."""

import json
import pytest
from pathlib import Path

from qa_agent.models.base import RequirementType
from qa_agent.parsers.openapi_parser import OpenAPIParser


# Sample valid OpenAPI 3.0 specification
VALID_OPENAPI_3 = """{
  "openapi": "3.0.0",
  "info": {
    "title": "Sample API",
    "version": "1.0.0",
    "description": "A sample API for testing"
  },
  "paths": {
    "/users": {
      "get": {
        "summary": "List all users",
        "description": "Returns a list of all users",
        "operationId": "listUsers",
        "parameters": [
          {
            "name": "limit",
            "in": "query",
            "description": "Maximum number of users",
            "required": false,
            "schema": {
              "type": "integer",
              "minimum": 1,
              "maximum": 100,
              "default": 20
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Successful response",
            "content": {
              "application/json": {
                "schema": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "id": {"type": "integer"},
                      "name": {"type": "string"}
                    }
                  }
                }
              }
            }
          }
        }
      },
      "post": {
        "summary": "Create a user",
        "operationId": "createUser",
        "requestBody": {
          "description": "User to create",
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "properties": {
                  "name": {"type": "string", "minLength": 1},
                  "email": {"type": "string", "format": "email"}
                },
                "required": ["name", "email"]
              }
            }
          }
        },
        "responses": {
          "201": {
            "description": "User created"
          }
        }
      }
    }
  }
}"""

# Sample Swagger 2.0 specification
VALID_SWAGGER_2 = """{
  "swagger": "2.0",
  "info": {
    "title": "Sample API",
    "version": "1.0.0"
  },
  "paths": {
    "/users": {
      "get": {
        "summary": "List users",
        "operationId": "listUsers",
        "responses": {
          "200": {
            "description": "Success",
            "schema": {
              "type": "array",
              "items": {
                "type": "object"
              }
            }
          }
        }
      }
    }
  }
}"""

# Minimal valid spec
MINIMAL_SPEC = """{
  "openapi": "3.0.0",
  "info": {
    "title": "Minimal API",
    "version": "1.0.0"
  },
  "paths": {}
}"""

# Invalid JSON/YAML
INVALID_JSON = """{ "openapi": "3.0.0", "info": { "title": "Test" """

# Missing required fields
MISSING_INFO = """{
  "openapi": "3.0.0",
  "paths": {}
}"""

MISSING_PATHS = """{
  "openapi": "3.0.0",
  "info": {
    "title": "Test",
    "version": "1.0.0"
  }
}"""

# No version field
NO_VERSION = """{
  "info": {
    "title": "Test",
    "version": "1.0.0"
  },
  "paths": {}
}"""


class TestOpenAPIParser:
    """Tests for OpenAPIParser class."""

    def test_parser_metadata(self):
        """Test that parser has correct metadata."""
        parser = OpenAPIParser()
        assert parser.name == "openapi"
        assert ".json" in parser.supported_extensions
        assert ".yaml" in parser.supported_extensions
        assert ".yml" in parser.supported_extensions
        assert "OpenAPI" in parser.description or "Swagger" in parser.description

    def test_parse_valid_openapi_3(self):
        """Test parsing a valid OpenAPI 3.0 specification."""
        parser = OpenAPIParser()
        requirements = parser.parse(VALID_OPENAPI_3)

        # Should return 2 requirements (GET /users and POST /users)
        assert len(requirements) == 2

        # Check GET endpoint
        get_req = next(r for r in requirements if r.metadata["method"] == "GET")
        assert get_req.type == RequirementType.API_ENDPOINT
        assert get_req.id == "API-listUsers"
        assert get_req.metadata["path"] == "/users"
        assert get_req.metadata["operation_id"] == "listUsers"
        assert get_req.metadata["summary"] == "List all users"
        assert get_req.metadata["description"] == "Returns a list of all users"
        assert get_req.metadata["openapi_version"] == "3.0.0"
        assert len(get_req.metadata["parameters"]) == 1
        assert "200" in get_req.metadata["responses"]

        # Check parameter details
        param = get_req.metadata["parameters"][0]
        assert param["name"] == "limit"
        assert param["in"] == "query"
        assert param["required"] is False
        assert param["type"] == "integer"
        assert param["minimum"] == 1
        assert param["maximum"] == 100
        assert param["default"] == 20

        # Check POST endpoint
        post_req = next(r for r in requirements if r.metadata["method"] == "POST")
        assert post_req.type == RequirementType.API_ENDPOINT
        assert post_req.id == "API-createUser"
        assert post_req.metadata["path"] == "/users"
        assert post_req.metadata["request_body"] is not None
        assert post_req.metadata["request_body"]["required"] is True
        assert "201" in post_req.metadata["responses"]

    def test_parse_swagger_2(self):
        """Test parsing a Swagger 2.0 specification."""
        parser = OpenAPIParser()
        requirements = parser.parse(VALID_SWAGGER_2)

        assert len(requirements) == 1

        req = requirements[0]
        assert req.type == RequirementType.API_ENDPOINT
        assert req.metadata["openapi_version"] == "2.0"
        assert req.metadata["method"] == "GET"
        assert req.metadata["path"] == "/users"

    def test_parse_from_file(self, tmp_path):
        """Test parsing from a file."""
        test_file = tmp_path / "api.json"
        test_file.write_text(VALID_OPENAPI_3, encoding="utf-8")

        parser = OpenAPIParser()
        requirements = parser.parse(test_file)

        assert len(requirements) == 2
        assert requirements[0].source == str(test_file)

    def test_parse_nonexistent_file(self):
        """Test parsing a non-existent file raises error."""
        parser = OpenAPIParser()
        with pytest.raises(FileNotFoundError):
            parser.parse(Path("/nonexistent/api.json"))

    def test_parse_invalid_json(self):
        """Test parsing invalid JSON raises error."""
        parser = OpenAPIParser()
        with pytest.raises(ValueError, match="Invalid OpenAPI specification"):
            parser.parse(INVALID_JSON)

    def test_parse_missing_required_fields(self):
        """Test parsing spec with missing required fields."""
        parser = OpenAPIParser()
        
        # Missing info should fail validation
        with pytest.raises(ValueError, match="Invalid OpenAPI specification"):
            parser.parse(MISSING_INFO)
        
        # Missing paths should fail validation
        with pytest.raises(ValueError, match="Invalid OpenAPI specification"):
            parser.parse(MISSING_PATHS)

    def test_validate_valid_spec(self):
        """Test validating a valid specification."""
        parser = OpenAPIParser()
        result = parser.validate(VALID_OPENAPI_3)

        assert result.is_valid
        assert len(result.errors) == 0

    def test_validate_minimal_spec(self):
        """Test validating a minimal valid specification."""
        parser = OpenAPIParser()
        result = parser.validate(MINIMAL_SPEC)

        assert result.is_valid
        # May have warnings about empty paths
        assert len(result.errors) == 0

    def test_validate_invalid_json(self):
        """Test validating invalid JSON."""
        parser = OpenAPIParser()
        result = parser.validate(INVALID_JSON)

        assert not result.is_valid
        assert any("JSON" in error or "YAML" in error for error in result.errors)

    def test_validate_missing_info(self):
        """Test validating spec without info section."""
        parser = OpenAPIParser()
        result = parser.validate(MISSING_INFO)

        assert not result.is_valid
        assert any("info" in error.lower() for error in result.errors)

    def test_validate_missing_paths(self):
        """Test validating spec without paths section."""
        parser = OpenAPIParser()
        result = parser.validate(MISSING_PATHS)

        assert not result.is_valid
        assert any("paths" in error.lower() for error in result.errors)

    def test_validate_no_version(self):
        """Test validating spec without version field."""
        parser = OpenAPIParser()
        result = parser.validate(NO_VERSION)

        assert not result.is_valid
        assert any("openapi" in error.lower() or "swagger" in error.lower() for error in result.errors)

    def test_validate_empty_content(self):
        """Test validating empty content."""
        parser = OpenAPIParser()
        result = parser.validate("")

        assert not result.is_valid
        assert any("empty" in error.lower() for error in result.errors)

    def test_validate_from_file(self, tmp_path):
        """Test validating from a file."""
        test_file = tmp_path / "api.json"
        test_file.write_text(VALID_OPENAPI_3, encoding="utf-8")

        parser = OpenAPIParser()
        result = parser.validate(test_file)

        assert result.is_valid

    def test_validate_nonexistent_file(self):
        """Test validating a non-existent file."""
        parser = OpenAPIParser()
        result = parser.validate(Path("/nonexistent/api.json"))

        assert not result.is_valid
        assert any("not found" in error.lower() for error in result.errors)

    def test_supports_file(self):
        """Test file extension support."""
        parser = OpenAPIParser()

        assert parser.supports_file(Path("api.json"))
        assert parser.supports_file(Path("api.yaml"))
        assert parser.supports_file(Path("api.yml"))
        assert not parser.supports_file(Path("api.txt"))
        assert not parser.supports_file(Path("api.md"))

    def test_get_metadata(self):
        """Test getting parser metadata."""
        parser = OpenAPIParser()
        metadata = parser.get_metadata()

        assert metadata["name"] == "openapi"
        assert ".json" in metadata["supported_extensions"]
        assert "description" in metadata

    def test_endpoint_id_generation(self):
        """Test that endpoint IDs are generated correctly."""
        parser = OpenAPIParser()
        requirements = parser.parse(VALID_OPENAPI_3)

        # Check that operation IDs are used
        ids = [r.id for r in requirements]
        assert "API-listUsers" in ids
        assert "API-createUser" in ids

    def test_endpoint_without_operation_id(self):
        """Test parsing endpoint without operationId."""
        spec = """{
          "openapi": "3.0.0",
          "info": {"title": "Test", "version": "1.0.0"},
          "paths": {
            "/test": {
              "get": {
                "summary": "Test endpoint",
                "responses": {"200": {"description": "OK"}}
              }
            }
          }
        }"""
        
        parser = OpenAPIParser()
        requirements = parser.parse(spec)

        assert len(requirements) == 1
        # Should generate ID from method and path
        assert "get" in requirements[0].id.lower() or "test" in requirements[0].id.lower()

    def test_path_level_parameters(self):
        """Test parsing path-level parameters."""
        spec = """{
          "openapi": "3.0.0",
          "info": {"title": "Test", "version": "1.0.0"},
          "paths": {
            "/users/{userId}": {
              "parameters": [
                {
                  "name": "userId",
                  "in": "path",
                  "required": true,
                  "schema": {"type": "integer"}
                }
              ],
              "get": {
                "summary": "Get user",
                "responses": {"200": {"description": "OK"}}
              }
            }
          }
        }"""
        
        parser = OpenAPIParser()
        requirements = parser.parse(spec)

        assert len(requirements) == 1
        # Path-level parameter should be included
        assert len(requirements[0].metadata["parameters"]) == 1
        assert requirements[0].metadata["parameters"][0]["name"] == "userId"
        assert requirements[0].metadata["parameters"][0]["in"] == "path"
        assert requirements[0].metadata["parameters"][0]["required"] is True

    def test_multiple_response_codes(self):
        """Test parsing multiple response codes."""
        spec = """{
          "openapi": "3.0.0",
          "info": {"title": "Test", "version": "1.0.0"},
          "paths": {
            "/users": {
              "get": {
                "summary": "List users",
                "responses": {
                  "200": {"description": "Success"},
                  "400": {"description": "Bad request"},
                  "401": {"description": "Unauthorized"},
                  "500": {"description": "Server error"}
                }
              }
            }
          }
        }"""
        
        parser = OpenAPIParser()
        requirements = parser.parse(spec)

        assert len(requirements) == 1
        responses = requirements[0].metadata["responses"]
        assert "200" in responses
        assert "400" in responses
        assert "401" in responses
        assert "500" in responses

    def test_parameter_constraints(self):
        """Test that parameter constraints are extracted."""
        spec = """{
          "openapi": "3.0.0",
          "info": {"title": "Test", "version": "1.0.0"},
          "paths": {
            "/users": {
              "get": {
                "summary": "List users",
                "parameters": [
                  {
                    "name": "name",
                    "in": "query",
                    "schema": {
                      "type": "string",
                      "minLength": 1,
                      "maxLength": 50,
                      "pattern": "^[a-zA-Z]+$"
                    }
                  },
                  {
                    "name": "status",
                    "in": "query",
                    "schema": {
                      "type": "string",
                      "enum": ["active", "inactive", "pending"]
                    }
                  }
                ],
                "responses": {"200": {"description": "OK"}}
              }
            }
          }
        }"""
        
        parser = OpenAPIParser()
        requirements = parser.parse(spec)

        params = requirements[0].metadata["parameters"]
        
        # Check string constraints
        name_param = next(p for p in params if p["name"] == "name")
        assert name_param["minLength"] == 1
        assert name_param["maxLength"] == 50
        assert name_param["pattern"] == "^[a-zA-Z]+$"
        
        # Check enum constraint
        status_param = next(p for p in params if p["name"] == "status")
        assert status_param["enum"] == ["active", "inactive", "pending"]

    def test_request_body_schema(self):
        """Test that request body schema is extracted."""
        parser = OpenAPIParser()
        requirements = parser.parse(VALID_OPENAPI_3)

        post_req = next(r for r in requirements if r.metadata["method"] == "POST")
        request_body = post_req.metadata["request_body"]
        
        assert request_body is not None
        assert request_body["required"] is True
        assert "application/json" in request_body["content"]
        
        schema = request_body["content"]["application/json"]["schema"]
        assert schema["type"] == "object"
        assert "name" in schema["properties"]
        assert "email" in schema["properties"]
        assert schema["required"] == ["name", "email"]

    def test_response_schema(self):
        """Test that response schema is extracted."""
        parser = OpenAPIParser()
        requirements = parser.parse(VALID_OPENAPI_3)

        get_req = next(r for r in requirements if r.metadata["method"] == "GET")
        responses = get_req.metadata["responses"]
        
        assert "200" in responses
        response_200 = responses["200"]
        assert response_200["description"] == "Successful response"
        assert "application/json" in response_200["content"]
        
        schema = response_200["content"]["application/json"]["schema"]
        assert schema["type"] == "array"
        assert schema["items"]["type"] == "object"

    def test_api_metadata(self):
        """Test that API-level metadata is included."""
        parser = OpenAPIParser()
        requirements = parser.parse(VALID_OPENAPI_3)

        for req in requirements:
            assert req.metadata["api_title"] == "Sample API"
            assert req.metadata["api_version"] == "1.0.0"
            assert req.metadata["openapi_version"] == "3.0.0"

    def test_content_description(self):
        """Test that content field contains useful information."""
        parser = OpenAPIParser()
        requirements = parser.parse(VALID_OPENAPI_3)

        get_req = next(r for r in requirements if r.metadata["method"] == "GET")
        
        assert "GET /users" in get_req.content
        assert "List all users" in get_req.content
        assert "Returns a list of all users" in get_req.content


class TestOpenAPIParserIntegration:
    """Integration tests for OpenAPI parser."""

    def test_parser_registration(self):
        """Test that OpenAPI parser can be registered and retrieved."""
        from qa_agent.parsers.base import ParserRegistry

        registry = ParserRegistry()
        registry.register(OpenAPIParser)

        assert registry.is_registered("openapi")

        parser = registry.get_parser("openapi")
        assert isinstance(parser, OpenAPIParser)

    def test_parser_file_detection(self):
        """Test that parser is selected for API spec files."""
        from qa_agent.parsers.base import ParserRegistry

        registry = ParserRegistry()
        registry.register(OpenAPIParser)

        parser = registry.get_parser_for_file(Path("api.json"))
        assert isinstance(parser, OpenAPIParser)

        parser = registry.get_parser_for_file(Path("api.yaml"))
        assert isinstance(parser, OpenAPIParser)

    def test_end_to_end_workflow(self, tmp_path):
        """Test complete workflow from file to parsed requirements."""
        from qa_agent.parsers.base import ParserRegistry

        # Create test file
        test_file = tmp_path / "api.json"
        test_file.write_text(VALID_OPENAPI_3, encoding="utf-8")

        # Register parser
        registry = ParserRegistry()
        registry.register(OpenAPIParser)

        # Get parser for file
        parser = registry.get_parser_for_file(test_file)
        assert parser is not None

        # Validate
        validation = parser.validate(test_file)
        assert validation.is_valid

        # Parse
        requirements = parser.parse(test_file)
        assert len(requirements) == 2

        # Verify structure
        for req in requirements:
            assert req.type == RequirementType.API_ENDPOINT
            assert "method" in req.metadata
            assert "path" in req.metadata
            assert "responses" in req.metadata

    def test_yaml_format_support(self, tmp_path):
        """Test parsing YAML format specifications."""
        yaml_spec = """
openapi: 3.0.0
info:
  title: YAML API
  version: 1.0.0
paths:
  /test:
    get:
      summary: Test endpoint
      responses:
        '200':
          description: OK
"""
        test_file = tmp_path / "api.yaml"
        test_file.write_text(yaml_spec, encoding="utf-8")

        parser = OpenAPIParser()
        requirements = parser.parse(test_file)

        assert len(requirements) == 1
        assert requirements[0].metadata["api_title"] == "YAML API"
