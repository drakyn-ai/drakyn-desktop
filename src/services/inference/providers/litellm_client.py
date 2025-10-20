"""
LiteLLM client wrapper for multi-provider LLM support.
Provides unified interface for vLLM, OpenAI, Anthropic, and others.
"""
import logging
from typing import List, Optional, Dict, Any
from litellm import acompletion
from agent.models import Message, CompletionConfig

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

        # Log message count and size for debugging
        total_chars = sum(len(msg.content) for msg in messages)
        logger.info(f"Sending {len(messages)} messages ({total_chars} chars total)")

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
        # NOTE: Many models (especially Ollama) don't support native function calling
        # We handle tools via system prompt instead
        if tools and False:  # Disabled for now - using prompt-based tools instead
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
            logger.info(f"Sending {len(tools)} tools to LiteLLM")

        # Add stop sequences if configured
        if config.stop:
            kwargs["stop"] = config.stop

        try:
            logger.info(f"Calling LiteLLM with model: {config.model}, api_base: {self.api_base}")

            # Enable LiteLLM debug logging
            import litellm
            litellm.set_verbose = True

            # Log first 500 chars of each message for debugging
            for i, msg in enumerate(formatted_messages):
                preview = msg['content'][:500] if len(msg['content']) > 500 else msg['content']
                logger.debug(f"Message {i} ({msg['role']}): {preview}...")

            import time
            import asyncio
            start_time = time.time()

            # Add timeout to prevent hanging forever
            try:
                response = await asyncio.wait_for(acompletion(**kwargs), timeout=60.0)
            except asyncio.TimeoutError:
                logger.error("LiteLLM call timed out after 60 seconds")
                raise Exception("LLM request timed out after 60 seconds")

            elapsed = time.time() - start_time

            logger.info(f"LiteLLM response received in {elapsed:.2f}s")

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


class OllamaClient(LiteLLMClient):
    """
    Convenience wrapper for Ollama server.
    Pre-configured with Ollama defaults and proper model prefix.
    """

    def __init__(self, api_base: Optional[str] = None):
        """
        Initialize Ollama client.

        Args:
            api_base: Ollama server URL (default from env or http://localhost:11434)
        """
        import os
        if not api_base:
            api_base = os.getenv("OPENAI_COMPATIBLE_URL", "http://localhost:11434")

        super().__init__(
            api_base=api_base,
            api_key="ollama"  # Ollama doesn't require real API key
        )

    async def complete(
        self,
        messages: List[Message],
        config: CompletionConfig,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Get completion from Ollama.
        Ensures model name has ollama/ prefix for LiteLLM routing.
        """
        # Add ollama/ prefix if not already present
        if not config.model.startswith("ollama/"):
            config.model = f"ollama/{config.model}"
        return await super().complete(messages, config, tools)
