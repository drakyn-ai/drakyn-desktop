"""
LiteLLM client wrapper for multi-provider LLM support.
Provides unified interface for vLLM, OpenAI, Anthropic, and others.
"""
import logging
from typing import List, Optional, Dict, Any
from litellm import acompletion
from ..agent.models import Message, CompletionConfig

logger = logging.getLogger(__name__)


class LiteLLMClient:
    """
    Wrapper around LiteLLM for consistent LLM access.

    Supports:
    - Local vLLM models (openai/model-name)
    - OpenAI models (openai/gpt-4)
    - Anthropic models (anthropic/claude-3-5-sonnet-20241022)
    - And many others via LiteLLM
    """

    def __init__(
        self,
        api_base: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        """
        Initialize LiteLLM client.

        Args:
            api_base: Base URL for local models (e.g., http://localhost:8000/v1)
            api_key: API key for cloud providers (optional for local models)
        """
        self.api_base = api_base
        self.api_key = api_key or "dummy"  # vLLM doesn't need real key

    async def complete(
        self,
        messages: List[Message],
        config: CompletionConfig,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Get completion from LLM.

        Args:
            messages: Conversation history
            config: Completion configuration
            tools: Optional tool definitions for function calling

        Returns:
            Model's text response
        """
        # Convert Message objects to dict format
        formatted_messages = [
            {
                "role": msg.role,
                "content": msg.content,
                **({"name": msg.name} if msg.name else {})
            }
            for msg in messages
        ]

        # Prepare completion kwargs
        kwargs = {
            "model": config.model,
            "messages": formatted_messages,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "top_p": config.top_p,
            "stream": False,  # We handle streaming at orchestrator level
        }

        # Add API config if using local server
        if self.api_base:
            kwargs["api_base"] = self.api_base
            kwargs["api_key"] = self.api_key

        # Add tools if provided (for function calling)
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        # Add stop sequences if configured
        if config.stop:
            kwargs["stop"] = config.stop

        try:
            logger.debug(f"Calling LiteLLM with model: {config.model}")

            response = await acompletion(**kwargs)

            # Extract content from response
            if hasattr(response, 'choices') and len(response.choices) > 0:
                choice = response.choices[0]

                # Check for function call
                if hasattr(choice.message, 'tool_calls') and choice.message.tool_calls:
                    # Model wants to call a tool
                    tool_call = choice.message.tool_calls[0]
                    # Return as JSON string for consistent parsing
                    import json
                    return json.dumps({
                        "tool": tool_call.function.name,
                        "args": json.loads(tool_call.function.arguments),
                        "reasoning": "Tool call requested by model"
                    })

                # Regular text response
                return choice.message.content or ""

            logger.error("Unexpected response format from LiteLLM")
            return "Error: Unexpected response format"

        except Exception as e:
            logger.error(f"LiteLLM completion failed: {str(e)}")
            raise


class vLLMClient(LiteLLMClient):
    """
    Convenience wrapper for local vLLM server.
    Pre-configured with localhost defaults.
    """

    def __init__(self, port: int = 8000):
        """
        Initialize vLLM client.

        Args:
            port: vLLM server port (default 8000)
        """
        super().__init__(
            api_base=f"http://localhost:{port}/v1",
            api_key="dummy"  # vLLM doesn't require real API key
        )
