"""Tests for LLM client implementation."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from qa_agent.config.loader import AIConfig
from qa_agent.llm.client import APIError, LLMClient, LLMError, RateLimitError


class TestLLMClientInitialization:
    """Tests for LLM client initialization."""

    def test_init_kiro_provider(self):
        """Test initialization with Kiro provider."""
        config = AIConfig(provider="kiro", model="auto")
        client = LLMClient(config)

        assert client.provider == "kiro"
        assert client.model == "auto"
        assert client.temperature == 0.7
        assert client.max_tokens == 2000
        assert client._client is None

    def test_init_openai_provider_with_api_key(self):
        """Test initialization with OpenAI provider and API key."""
        config = AIConfig(provider="openai", api_key="test-key", model="gpt-4")
        
        with patch("qa_agent.llm.client.AsyncOpenAI") as mock_openai:
            client = LLMClient(config)

            assert client.provider == "openai"
            assert client.model == "gpt-4"
            mock_openai.assert_called_once_with(api_key="test-key")

    def test_init_openai_provider_without_api_key(self):
        """Test initialization with OpenAI provider but no API key raises error."""
        # This should be caught by AIConfig validation
        with pytest.raises(ValueError, match="OpenAI provider requires an API key"):
            AIConfig(provider="openai", model="gpt-4")

    def test_init_openai_without_package(self):
        """Test initialization with OpenAI when package is not installed."""
        config = AIConfig(provider="openai", api_key="test-key", model="gpt-4")
        
        with patch("qa_agent.llm.client.AsyncOpenAI", side_effect=ImportError):
            with pytest.raises(ImportError, match="OpenAI provider requires the 'openai' package"):
                LLMClient(config)

    def test_init_custom_parameters(self):
        """Test initialization with custom temperature and max_tokens."""
        config = AIConfig(
            provider="kiro",
            model="quality",
            temperature=0.3,
            max_tokens=1000,
        )
        client = LLMClient(config)

        assert client.temperature == 0.3
        assert client.max_tokens == 1000


class TestLLMClientGeneration:
    """Tests for LLM client text generation."""

    @pytest.mark.asyncio
    async def test_generate_kiro_not_implemented(self):
        """Test that Kiro generation raises NotImplementedError."""
        config = AIConfig(provider="kiro", model="auto")
        client = LLMClient(config)

        with pytest.raises(LLMError, match="Kiro provider integration is not yet implemented"):
            await client.generate("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_openai_success(self):
        """Test successful OpenAI generation."""
        config = AIConfig(provider="openai", api_key="test-key", model="gpt-4")
        
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Generated response"

        with patch("qa_agent.llm.client.AsyncOpenAI") as mock_openai_class:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai_class.return_value = mock_client

            client = LLMClient(config)
            result = await client.generate("Test prompt")

            assert result == "Generated response"
            mock_client.chat.completions.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_openai_with_system_prompt(self):
        """Test OpenAI generation with system prompt."""
        config = AIConfig(provider="openai", api_key="test-key", model="gpt-4")
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Generated response"

        with patch("qa_agent.llm.client.AsyncOpenAI") as mock_openai_class:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai_class.return_value = mock_client

            client = LLMClient(config)
            result = await client.generate(
                "Test prompt",
                system_prompt="You are a helpful assistant"
            )

            assert result == "Generated response"
            
            # Verify system prompt was included
            call_args = mock_client.chat.completions.create.call_args
            messages = call_args.kwargs["messages"]
            assert len(messages) == 2
            assert messages[0]["role"] == "system"
            assert messages[0]["content"] == "You are a helpful assistant"
            assert messages[1]["role"] == "user"
            assert messages[1]["content"] == "Test prompt"

    @pytest.mark.asyncio
    async def test_generate_openai_empty_response(self):
        """Test OpenAI generation with empty response raises error."""
        config = AIConfig(provider="openai", api_key="test-key", model="gpt-4")
        
        mock_response = MagicMock()
        mock_response.choices = []

        with patch("qa_agent.llm.client.AsyncOpenAI") as mock_openai_class:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai_class.return_value = mock_client

            client = LLMClient(config)
            
            with pytest.raises(APIError, match="No response choices returned"):
                await client.generate("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_openai_none_content(self):
        """Test OpenAI generation with None content raises error."""
        config = AIConfig(provider="openai", api_key="test-key", model="gpt-4")
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None

        with patch("qa_agent.llm.client.AsyncOpenAI") as mock_openai_class:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai_class.return_value = mock_client

            client = LLMClient(config)
            
            with pytest.raises(APIError, match="Empty response content"):
                await client.generate("Test prompt")


class TestLLMClientRetryLogic:
    """Tests for LLM client retry logic and error handling."""

    @pytest.mark.asyncio
    async def test_retry_on_rate_limit(self):
        """Test retry logic on rate limit error."""
        config = AIConfig(provider="openai", api_key="test-key", model="gpt-4")
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Success"

        with patch("qa_agent.llm.client.AsyncOpenAI") as mock_openai_class:
            mock_client = AsyncMock()
            # First call raises rate limit, second succeeds
            mock_client.chat.completions.create = AsyncMock(
                side_effect=[
                    Exception("Rate limit exceeded"),
                    mock_response,
                ]
            )
            mock_openai_class.return_value = mock_client

            client = LLMClient(config)
            
            # Should succeed after retry
            result = await client.generate("Test prompt", max_retries=3, retry_delay=0.1)
            assert result == "Success"
            assert mock_client.chat.completions.create.call_count == 2

    @pytest.mark.asyncio
    async def test_retry_exhausted_rate_limit(self):
        """Test that rate limit error is raised after exhausting retries."""
        config = AIConfig(provider="openai", api_key="test-key", model="gpt-4")

        with patch("qa_agent.llm.client.AsyncOpenAI") as mock_openai_class:
            mock_client = AsyncMock()
            # Always raise rate limit error
            mock_client.chat.completions.create = AsyncMock(
                side_effect=Exception("Rate limit exceeded")
            )
            mock_openai_class.return_value = mock_client

            client = LLMClient(config)
            
            with pytest.raises(RateLimitError, match="Rate limit exceeded"):
                await client.generate("Test prompt", max_retries=2, retry_delay=0.1)
            
            # Should have tried max_retries times
            assert mock_client.chat.completions.create.call_count == 2

    @pytest.mark.asyncio
    async def test_retry_on_api_error(self):
        """Test retry logic on API error."""
        config = AIConfig(provider="openai", api_key="test-key", model="gpt-4")
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Success"

        with patch("qa_agent.llm.client.AsyncOpenAI") as mock_openai_class:
            mock_client = AsyncMock()
            # First call raises API error, second succeeds
            mock_client.chat.completions.create = AsyncMock(
                side_effect=[
                    Exception("API connection error"),
                    mock_response,
                ]
            )
            mock_openai_class.return_value = mock_client

            client = LLMClient(config)
            
            result = await client.generate("Test prompt", max_retries=3, retry_delay=0.1)
            assert result == "Success"
            assert mock_client.chat.completions.create.call_count == 2

    @pytest.mark.asyncio
    async def test_exponential_backoff(self):
        """Test that retry delay increases exponentially."""
        config = AIConfig(provider="openai", api_key="test-key", model="gpt-4")

        with patch("qa_agent.llm.client.AsyncOpenAI") as mock_openai_class:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(
                side_effect=Exception("Rate limit exceeded")
            )
            mock_openai_class.return_value = mock_client

            client = LLMClient(config)
            
            with patch("asyncio.sleep") as mock_sleep:
                try:
                    await client.generate("Test prompt", max_retries=3, retry_delay=1.0)
                except RateLimitError:
                    pass
                
                # Check exponential backoff: 1.0, 2.0
                assert mock_sleep.call_count == 2
                calls = [call.args[0] for call in mock_sleep.call_args_list]
                assert calls[0] == 1.0  # First retry: 1.0 * 2^0
                assert calls[1] == 2.0  # Second retry: 1.0 * 2^1


class TestLLMClientSyncWrapper:
    """Tests for synchronous wrapper method."""

    def test_generate_sync(self):
        """Test synchronous generation wrapper."""
        config = AIConfig(provider="openai", api_key="test-key", model="gpt-4")
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Generated response"

        with patch("qa_agent.llm.client.AsyncOpenAI") as mock_openai_class:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai_class.return_value = mock_client

            client = LLMClient(config)
            result = client.generate_sync("Test prompt")

            assert result == "Generated response"


class TestLLMClientParameters:
    """Tests for parameter handling."""

    @pytest.mark.asyncio
    async def test_custom_parameters_passed_to_api(self):
        """Test that custom parameters are passed to the API."""
        config = AIConfig(
            provider="openai",
            api_key="test-key",
            model="gpt-4",
            temperature=0.5,
            max_tokens=1500,
        )
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"

        with patch("qa_agent.llm.client.AsyncOpenAI") as mock_openai_class:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai_class.return_value = mock_client

            client = LLMClient(config)
            await client.generate("Test prompt")

            # Verify parameters
            call_args = mock_client.chat.completions.create.call_args
            assert call_args.kwargs["model"] == "gpt-4"
            assert call_args.kwargs["temperature"] == 0.5
            assert call_args.kwargs["max_tokens"] == 1500

    @pytest.mark.asyncio
    async def test_additional_kwargs_passed_to_api(self):
        """Test that additional kwargs are passed to the API."""
        config = AIConfig(provider="openai", api_key="test-key", model="gpt-4")
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"

        with patch("qa_agent.llm.client.AsyncOpenAI") as mock_openai_class:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai_class.return_value = mock_client

            client = LLMClient(config)
            await client.generate("Test prompt", top_p=0.9, presence_penalty=0.5)

            # Verify additional parameters
            call_args = mock_client.chat.completions.create.call_args
            assert call_args.kwargs["top_p"] == 0.9
            assert call_args.kwargs["presence_penalty"] == 0.5
