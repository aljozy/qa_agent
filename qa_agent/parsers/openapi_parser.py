"""OpenAPI/Swagger specification parser implementation."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from qa_agent.models.base import Requirement, RequirementType, ValidationResult
from qa_agent.parsers.base import RequirementParser, register_parser


class OpenAPIParser(RequirementParser):
    """Parser for OpenAPI and Swagger specifications.
    
    Parses OpenAPI 2.0 (Swagger) and OpenAPI 3.x specifications, extracting:
    - API endpoints (paths)
    - HTTP methods (GET, POST, PUT, DELETE, etc.)
    - Request parameters (path, query, header, body)
    - Parameter constraints (required, type, format, enum, etc.)
    - Response schemas (status codes, response bodies)
    - Authentication/security requirements
    
    Each endpoint/method combination is treated as a separate requirement
    with type API_ENDPOINT.
    
    Supports both JSON and YAML formats.
    """

    name = "openapi"
    supported_extensions = [".json", ".yaml", ".yml"]
    description = "Parser for OpenAPI/Swagger API specifications"

    def parse(self, input_data: str | Path) -> List[Requirement]:
        """Parse OpenAPI specification and return structured requirements.
        
        Args:
            input_data: Either a string containing the spec content (JSON/YAML),
                       or a Path to a spec file
        
        Returns:
            List of Requirement objects - one for each endpoint/method combination
        
        Raises:
            ValueError: If input_data is invalid or cannot be parsed
            FileNotFoundError: If input_data is a Path that doesn't exist
        """
        # Import prance here to avoid import errors if not installed
        try:
            from prance import ResolvingParser
        except ImportError:
            raise ImportError(
                "prance library is required for OpenAPI parsing. "
                "Install it with: pip install prance"
            )

        # Determine source and file path
        if isinstance(input_data, Path):
            if not input_data.exists():
                raise FileNotFoundError(f"File not found: {input_data}")
            spec_path = str(input_data)
            source = str(input_data)
        else:
            # For string input, write to temp file for prance
            import tempfile
            with tempfile.NamedTemporaryFile(
                mode='w', suffix='.json', delete=False, encoding='utf-8'
            ) as f:
                f.write(input_data)
                spec_path = f.name
            source = "string_input"

        # Validate before parsing
        validation = self.validate(input_data)
        if not validation.is_valid:
            error_msg = "; ".join(validation.errors)
            raise ValueError(f"Invalid OpenAPI specification: {error_msg}")

        # Parse the specification using prance (resolves $ref references)
        try:
            parser = ResolvingParser(spec_path, lazy=True, strict=False)
            parser.parse()
            spec = parser.specification
        except Exception as e:
            raise ValueError(f"Failed to parse OpenAPI specification: {str(e)}")
        finally:
            # Clean up temp file if we created one
            if isinstance(input_data, str):
                import os
                try:
                    os.unlink(spec_path)
                except:
                    pass

        # Extract requirements from the specification
        requirements = []
        
        # Get API metadata
        api_info = spec.get("info", {})
        api_title = api_info.get("title", "Untitled API")
        api_version = api_info.get("version", "unknown")
        
        # Determine OpenAPI version
        openapi_version = self._get_openapi_version(spec)
        
        # Extract paths (endpoints)
        paths = spec.get("paths", {})
        
        for path, path_item in paths.items():
            # Each HTTP method is a separate requirement
            for method, operation in path_item.items():
                # Skip non-method keys like 'parameters', 'summary', etc.
                if method.lower() not in ['get', 'post', 'put', 'delete', 'patch', 'options', 'head', 'trace']:
                    continue
                
                if not isinstance(operation, dict):
                    continue
                
                # Generate requirement ID
                operation_id = operation.get("operationId", f"{method}_{path}".replace("/", "_"))
                req_id = f"API-{operation_id}"
                
                # Extract operation details
                summary = operation.get("summary", "")
                description = operation.get("description", "")
                
                # Extract parameters
                parameters = self._extract_parameters(operation, path_item, openapi_version)
                
                # Extract request body (OpenAPI 3.x)
                request_body = self._extract_request_body(operation, openapi_version)
                
                # Extract responses
                responses = self._extract_responses(operation)
                
                # Extract security requirements
                security = self._extract_security(operation, spec)
                
                # Build content description
                content_parts = [
                    f"Endpoint: {method.upper()} {path}",
                ]
                if summary:
                    content_parts.append(f"Summary: {summary}")
                if description:
                    content_parts.append(f"Description: {description}")
                
                content = "\n".join(content_parts)
                
                # Create requirement
                requirement = Requirement(
                    id=req_id,
                    type=RequirementType.API_ENDPOINT,
                    content=content,
                    metadata={
                        "api_title": api_title,
                        "api_version": api_version,
                        "openapi_version": openapi_version,
                        "method": method.upper(),
                        "path": path,
                        "operation_id": operation_id,
                        "summary": summary,
                        "description": description,
                        "parameters": parameters,
                        "request_body": request_body,
                        "responses": responses,
                        "security": security,
                        "tags": operation.get("tags", []),
                    },
                    source=source,
                )
                requirements.append(requirement)
        
        return requirements

    def validate(self, input_data: str | Path) -> ValidationResult:
        """Validate OpenAPI specification format.
        
        Args:
            input_data: Either a string containing the spec content,
                       or a Path to a file to validate
        
        Returns:
            ValidationResult indicating whether the input is valid,
            along with any errors or warnings
        """
        errors = []
        warnings = []
        
        # Import prance here to avoid import errors if not installed
        try:
            from prance import ResolvingParser
        except ImportError:
            return ValidationResult(
                is_valid=False,
                errors=["prance library is required for OpenAPI parsing. Install it with: pip install prance"],
            )
        
        # Read content and determine file path
        if isinstance(input_data, Path):
            if not input_data.exists():
                return ValidationResult(
                    is_valid=False,
                    errors=[f"File not found: {input_data}"],
                )
            spec_path = str(input_data)
            try:
                with open(input_data, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception as e:
                return ValidationResult(
                    is_valid=False,
                    errors=[f"Error reading file: {str(e)}"],
                )
        else:
            content = input_data
            # Write to temp file for prance validation
            import tempfile
            with tempfile.NamedTemporaryFile(
                mode='w', suffix='.json', delete=False, encoding='utf-8'
            ) as f:
                f.write(content)
                spec_path = f.name
        
        # Check if content is empty
        if not content or not content.strip():
            errors.append("Specification content is empty")
            return ValidationResult(is_valid=False, errors=errors)
        
        # Try to parse as JSON or YAML
        spec_dict = None
        try:
            spec_dict = json.loads(content)
        except json.JSONDecodeError:
            # Try YAML
            try:
                import yaml
                spec_dict = yaml.safe_load(content)
            except Exception as yaml_error:
                errors.append(f"Invalid JSON/YAML format: {str(yaml_error)}")
                return ValidationResult(is_valid=False, errors=errors)
        
        # Check for OpenAPI/Swagger version
        if "openapi" not in spec_dict and "swagger" not in spec_dict:
            errors.append(
                "Missing 'openapi' or 'swagger' version field. "
                "This doesn't appear to be a valid OpenAPI/Swagger specification."
            )
        
        # Check for required fields
        if "info" not in spec_dict:
            errors.append("Missing required 'info' section")
        else:
            info = spec_dict["info"]
            if "title" not in info:
                warnings.append("Missing 'title' in info section")
            if "version" not in info:
                warnings.append("Missing 'version' in info section")
        
        if "paths" not in spec_dict:
            errors.append("Missing required 'paths' section")
        elif not spec_dict["paths"]:
            warnings.append("'paths' section is empty - no endpoints defined")
        
        # Try to parse with prance for detailed validation
        try:
            parser = ResolvingParser(spec_path, lazy=True, strict=False)
            parser.parse()
            # If we get here, the spec is valid
        except Exception as e:
            error_msg = str(e)
            # Extract location information if available
            if "at" in error_msg.lower() or "line" in error_msg.lower():
                errors.append(f"Validation error: {error_msg}")
            else:
                errors.append(f"Validation error: {error_msg}")
        finally:
            # Clean up temp file if we created one
            if isinstance(input_data, str):
                import os
                try:
                    os.unlink(spec_path)
                except:
                    pass
        
        # Determine validity
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            metadata={
                "content_length": len(content),
                "openapi_version": spec_dict.get("openapi") or spec_dict.get("swagger"),
            },
        )

    def _get_openapi_version(self, spec: Dict[str, Any]) -> str:
        """Determine OpenAPI version from specification.
        
        Args:
            spec: Parsed specification dictionary
        
        Returns:
            Version string (e.g., "3.0.0", "2.0")
        """
        if "openapi" in spec:
            return spec["openapi"]
        elif "swagger" in spec:
            return spec["swagger"]
        return "unknown"

    def _extract_parameters(
        self, 
        operation: Dict[str, Any], 
        path_item: Dict[str, Any],
        openapi_version: str
    ) -> List[Dict[str, Any]]:
        """Extract parameters from operation and path item.
        
        Parameters can be defined at the operation level or path level.
        Operation-level parameters override path-level parameters.
        
        Args:
            operation: Operation object
            path_item: Path item object
            openapi_version: OpenAPI version string
        
        Returns:
            List of parameter dictionaries with extracted details
        """
        parameters = []
        
        # Get path-level parameters
        path_params = path_item.get("parameters", [])
        
        # Get operation-level parameters
        op_params = operation.get("parameters", [])
        
        # Combine parameters (operation-level overrides path-level)
        all_params = list(path_params) + list(op_params)
        
        for param in all_params:
            param_info = {
                "name": param.get("name", ""),
                "in": param.get("in", ""),  # path, query, header, cookie
                "description": param.get("description", ""),
                "required": param.get("required", False),
                "deprecated": param.get("deprecated", False),
            }
            
            # Extract schema information
            if "schema" in param:
                schema = param["schema"]
                param_info["type"] = schema.get("type", "")
                param_info["format"] = schema.get("format", "")
                param_info["enum"] = schema.get("enum", [])
                param_info["minimum"] = schema.get("minimum")
                param_info["maximum"] = schema.get("maximum")
                param_info["minLength"] = schema.get("minLength")
                param_info["maxLength"] = schema.get("maxLength")
                param_info["pattern"] = schema.get("pattern")
                param_info["default"] = schema.get("default")
            elif "type" in param:
                # Swagger 2.0 style
                param_info["type"] = param.get("type", "")
                param_info["format"] = param.get("format", "")
                param_info["enum"] = param.get("enum", [])
                param_info["minimum"] = param.get("minimum")
                param_info["maximum"] = param.get("maximum")
                param_info["minLength"] = param.get("minLength")
                param_info["maxLength"] = param.get("maxLength")
                param_info["pattern"] = param.get("pattern")
                param_info["default"] = param.get("default")
            
            parameters.append(param_info)
        
        return parameters

    def _extract_request_body(
        self, 
        operation: Dict[str, Any],
        openapi_version: str
    ) -> Optional[Dict[str, Any]]:
        """Extract request body schema (OpenAPI 3.x).
        
        Args:
            operation: Operation object
            openapi_version: OpenAPI version string
        
        Returns:
            Request body information or None if not present
        """
        if "requestBody" not in operation:
            return None
        
        request_body = operation["requestBody"]
        
        body_info = {
            "description": request_body.get("description", ""),
            "required": request_body.get("required", False),
            "content": {},
        }
        
        # Extract content types and schemas
        content = request_body.get("content", {})
        for media_type, media_type_obj in content.items():
            schema = media_type_obj.get("schema", {})
            body_info["content"][media_type] = {
                "schema": self._simplify_schema(schema),
            }
        
        return body_info

    def _extract_responses(self, operation: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Extract response definitions.
        
        Args:
            operation: Operation object
        
        Returns:
            Dictionary mapping status codes to response information
        """
        responses = {}
        
        responses_obj = operation.get("responses", {})
        
        for status_code, response in responses_obj.items():
            response_info = {
                "description": response.get("description", ""),
                "headers": {},
                "content": {},
            }
            
            # Extract headers
            headers = response.get("headers", {})
            for header_name, header_obj in headers.items():
                response_info["headers"][header_name] = {
                    "description": header_obj.get("description", ""),
                    "schema": header_obj.get("schema", {}),
                }
            
            # Extract content (OpenAPI 3.x)
            if "content" in response:
                content = response["content"]
                for media_type, media_type_obj in content.items():
                    schema = media_type_obj.get("schema", {})
                    response_info["content"][media_type] = {
                        "schema": self._simplify_schema(schema),
                    }
            # Swagger 2.0 style
            elif "schema" in response:
                response_info["content"]["application/json"] = {
                    "schema": self._simplify_schema(response["schema"]),
                }
            
            responses[status_code] = response_info
        
        return responses

    def _extract_security(
        self, 
        operation: Dict[str, Any],
        spec: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract security requirements.
        
        Args:
            operation: Operation object
            spec: Full specification (for security definitions)
        
        Returns:
            List of security requirement dictionaries
        """
        security_requirements = []
        
        # Get operation-level security or fall back to global security
        security = operation.get("security", spec.get("security", []))
        
        for security_item in security:
            for scheme_name, scopes in security_item.items():
                security_requirements.append({
                    "scheme": scheme_name,
                    "scopes": scopes,
                })
        
        return security_requirements

    def _simplify_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Simplify schema object for metadata storage.
        
        Extracts key information from schema without full recursion.
        
        Args:
            schema: Schema object
        
        Returns:
            Simplified schema dictionary
        """
        simplified = {
            "type": schema.get("type", ""),
            "format": schema.get("format", ""),
            "description": schema.get("description", ""),
            "required": schema.get("required", []),
            "enum": schema.get("enum", []),
        }
        
        # Add properties for object types
        if schema.get("type") == "object" and "properties" in schema:
            simplified["properties"] = list(schema["properties"].keys())
        
        # Add items for array types
        if schema.get("type") == "array" and "items" in schema:
            items = schema["items"]
            simplified["items"] = {
                "type": items.get("type", ""),
                "format": items.get("format", ""),
            }
        
        return simplified


# Register the parser in the global registry
register_parser(OpenAPIParser)
