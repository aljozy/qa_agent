"""LLM client implementation supporting multiple AI providers."""

import asyncio
import logging
import time
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from qa_agent.config.loader import AIConfig

from qa_agent.core.exceptions import APIError, LLMError, RateLimitError
from qa_agent.core.logging_config import get_logger, log_exception, log_operation_complete, log_operation_failed, log_operation_start

# Import OpenAI at module level for proper mocking in tests
try:
    from openai import AsyncOpenAI
except ImportError:
    AsyncOpenAI = None

logger = get_logger(__name__)


class LLMClient:
    """
    LLM client supporting both Kiro and OpenAI providers.

    This client provides a unified interface for generating text using different
    AI providers with built-in retry logic, rate limiting handling, and error management.
    """

    def __init__(self, config: "AIConfig"):
        """
        Initialize the LLM client.

        Args:
            config: AI configuration containing provider, model, and parameters

        Raises:
            LLMError: If the provider is not supported or initialization fails
        """
        self.config = config
        self.provider = config.provider
        self.model = config.model
        self.temperature = config.temperature
        self.max_tokens = config.max_tokens

        logger.info(
            f"Initializing LLM client",
            extra={"extra_fields": {"provider": self.provider, "model": self.model}}
        )

        # Initialize provider-specific client
        if self.provider == "kiro":
            self._client = None  # Kiro uses built-in models, no external client needed
            logger.info(f"Initialized Kiro LLM client with model: {self.model}")
        elif self.provider == "openai":
            if AsyncOpenAI is None:
                raise LLMError(
                    "OpenAI provider requires the 'openai' package. "
                    "Install it with: pip install openai",
                    provider="openai",
                    details={"missing_package": "openai"}
                )
            
            if not config.api_key:
                raise LLMError(
                    "OpenAI provider requires an API key. "
                    "Please provide 'api_key' in the configuration.",
                    provider="openai",
                    details={"missing_field": "api_key"}
                )
            
            try:
                self._client = AsyncOpenAI(api_key=config.api_key)
                logger.info(f"Initialized OpenAI LLM client with model: {self.model}")
            except ImportError as e:
                raise LLMError(
                    "OpenAI provider requires the 'openai' package. "
                    "Install it with: pip install openai",
                    provider="openai",
                    details={"error": str(e)}
                ) from e
        else:
            raise LLMError(
                f"Unsupported provider: {self.provider}. "
                f"Supported providers are: 'kiro', 'openai'",
                provider=self.provider,
                details={"supported_providers": ["kiro", "openai"]}
            )

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        **kwargs: Any,
    ) -> str:
        """
        Generate text using the configured AI provider.

        This method implements retry logic with exponential backoff for handling
        transient errors and rate limiting.

        Args:
            prompt: The user prompt to generate from
            system_prompt: Optional system prompt to set context
            max_retries: Maximum number of retry attempts (default: 3)
            retry_delay: Initial delay between retries in seconds (default: 1.0)
            **kwargs: Additional provider-specific parameters

        Returns:
            Generated text response

        Raises:
            LLMError: If generation fails after all retries
            RateLimitError: If rate limit is exceeded and retries are exhausted
            APIError: If there's an API-related error
        """
        last_error = None

        for attempt in range(max_retries):
            try:
                if self.provider == "kiro":
                    return await self._generate_kiro(prompt, system_prompt, **kwargs)
                elif self.provider == "openai":
                    return await self._generate_openai(prompt, system_prompt, **kwargs)
            except RateLimitError as e:
                last_error = e
                if attempt < max_retries - 1:
                    # Exponential backoff
                    delay = retry_delay * (2**attempt)
                    logger.warning(
                        f"Rate limit exceeded (attempt {attempt + 1}/{max_retries}). "
                        f"Retrying in {delay:.1f} seconds..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Rate limit exceeded after {max_retries} attempts")
                    raise
            except APIError as e:
                last_error = e
                if attempt < max_retries - 1:
                    # Exponential backoff
                    delay = retry_delay * (2**attempt)
                    logger.warning(
                        f"API error (attempt {attempt + 1}/{max_retries}): {str(e)}. "
                        f"Retrying in {delay:.1f} seconds..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"API error after {max_retries} attempts: {str(e)}")
                    raise
            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error during generation: {str(e)}")
                raise LLMError(f"Generation failed: {str(e)}") from e

        # Should not reach here, but just in case
        if last_error:
            raise last_error
        raise LLMError("Generation failed for unknown reason")

    async def _generate_kiro(
        self, prompt: str, system_prompt: Optional[str] = None, **kwargs: Any
    ) -> str:
        """
        Generate text using Kiro's built-in models.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            **kwargs: Additional parameters

        Returns:
            Generated text

        Raises:
            LLMError: If generation fails
        """
        # For Kiro, we simulate the generation since it's built-in
        # In a real implementation, this would call Kiro's internal API
        try:
            # Placeholder for Kiro's actual implementation
            # This would be replaced with actual Kiro API calls
            logger.debug(f"Generating with Kiro model: {self.model}")
            
            # Simulate API call delay
            await asyncio.sleep(0.1)
            
            # In production, this would call Kiro's internal generation API
            # For now, we raise an error to indicate this needs implementation
            raise NotImplementedError(
                "Kiro provider integration is not yet implemented. "
                "Please use 'openai' provider or implement Kiro integration."
            )
        except Exception as e:
            logger.error(f"Kiro generation failed: {str(e)}")
            raise LLMError(f"Kiro generation failed: {str(e)}") from e

    async def _generate_openai(
        self, prompt: str, system_prompt: Optional[str] = None, **kwargs: Any
    ) -> str:
        """
        Generate text using OpenAI's API.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            **kwargs: Additional parameters

        Returns:
            Generated text

        Raises:
            RateLimitError: If rate limit is exceeded
            APIError: If there's an API error
        """
        try:
            # Build messages
            messages: List[Dict[str, str]] = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            # Merge kwargs with default parameters
            params = {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                **kwargs,
            }

            logger.debug(f"Calling OpenAI API with model: {self.model}")
            start_time = time.time()

            # Make API call
            response = await self._client.chat.completions.create(**params)

            elapsed_time = time.time() - start_time
            logger.debug(f"OpenAI API call completed in {elapsed_time:.2f}s")

            # Extract generated text
            if not response.choices:
                raise APIError("No response choices returned from OpenAI API")

            generated_text = response.choices[0].message.content
            if not generated_text:
                raise APIError("Empty response content from OpenAI API")

            return generated_text.strip()

        except Exception as e:
            # Handle OpenAI-specific errors
            error_message = str(e).lower()

            if "rate" in error_message and "limit" in error_message:
                logger.warning(f"Rate limit error: {str(e)}")
                raise RateLimitError(f"OpenAI rate limit exceeded: {str(e)}") from e
            elif "api" in error_message or "authentication" in error_message:
                logger.error(f"API error: {str(e)}")
                raise APIError(f"OpenAI API error: {str(e)}") from e
            else:
                logger.error(f"Unexpected OpenAI error: {str(e)}")
                raise APIError(f"OpenAI generation failed: {str(e)}") from e

    def generate_sync(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        **kwargs: Any,
    ) -> str:
        """
        Synchronous wrapper for generate() method.

        Args:
            prompt: The user prompt to generate from
            system_prompt: Optional system prompt to set context
            max_retries: Maximum number of retry attempts (default: 3)
            retry_delay: Initial delay between retries in seconds (default: 1.0)
            **kwargs: Additional provider-specific parameters

        Returns:
            Generated text response

        Raises:
            LLMError: If generation fails after all retries
        """
        return asyncio.run(
            self.generate(prompt, system_prompt, max_retries, retry_delay, **kwargs)
        )
