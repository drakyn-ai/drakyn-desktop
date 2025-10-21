"""
Direct Anthropic client wrapper.
Simplified version that uses Anthropic SDK directly instead of litellm.
"""
import logging
import os
from typing import List, Optional, Dict, Any
from anthropic import AsyncAnthropic
from agent.models import Message, CompletionConfig

logger = logging.getLogger(__name__)


class LiteLLMClient:
    """
    Direct Anthropic client (litellm removed due to import issues).

    For now, only supports Anthropic Claude models.
    """

    def __init__(
        self,
        api_base: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        """
        Initialize Anthropic client.

        Args:
            api_base: Not used for Anthropic (kept for compatibility)
            api_key: Anthropic API key (will use ANTHROPIC_API_KEY env var if not provided)
        """
        self.api_base = api_base
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment or arguments")

        self.client = AsyncAnthropic(api_key=self.api_key)

    async def complete(
        self,
        messages: List[Message],
        config: CompletionConfig,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Get completion from Anthropic Claude.

        Args:
            messages: Conversation history
            config: Completion configuration
            tools: Optional tool definitions (not used in this version)

        Returns:
            Model's text response
        """
        # Convert Message objects to Anthropic format
        # Separate system message from conversation messages
        system_message = None
        conversation_messages = []

        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
            elif msg.role == "user":
                conversation_messages.append({
                    "role": "user",
                    "content": msg.content
                })
            elif msg.role == "assistant":
                conversation_messages.append({
                    "role": "assistant",
                    "content": msg.content
                })
            elif msg.role == "tool":
                # Send tool results as user messages with text content
                # (our orchestrator uses text-based JSON tool calls, not Anthropic's native tool calling)
                tool_result_text = f"Tool '{msg.name}' returned:\n{msg.content}"
                conversation_messages.append({
                    "role": "user",
                    "content": tool_result_text
                })

        # Log message count and size for debugging
        total_chars = sum(len(msg.content) for msg in messages)
        logger.info(f"Sending {len(messages)} messages ({total_chars} chars total) to Anthropic")
        logger.info(f"Model: {config.model}, temperature: {config.temperature}")

        try:
            # Call Anthropic API
            response = await self.client.messages.create(
                model=config.model,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                system=system_message or "You are a helpful assistant.",
                messages=conversation_messages
            )

            logger.info(f"Received response from Anthropic, stop_reason: {response.stop_reason}")

            # Extract text content from response
            if response.content and len(response.content) > 0:
                text_content = []
                for block in response.content:
                    if hasattr(block, 'text'):
                        text_content.append(block.text)

                result = "\n".join(text_content) if text_content else ""

                if not result.strip():
                    logger.warning(f"Anthropic returned empty content: {response}")

                return result

            logger.error("Anthropic response had no content")
            return ""

        except Exception as e:
            logger.error(f"Anthropic API call failed: {str(e)}")
            raise


class vLLMClient(LiteLLMClient):
    """
    Placeholder for vLLM client (not implemented in this simplified version).
    """

    def __init__(self, port: int = 8000):
        logger.warning("vLLM client not implemented - using Anthropic fallback")
        super().__init__()


class OllamaClient(LiteLLMClient):
    """
    Placeholder for Ollama client (not implemented in this simplified version).
    """

    def __init__(self, api_base: Optional[str] = None):
        logger.warning("Ollama client not implemented - using Anthropic fallback")
        super().__init__()
