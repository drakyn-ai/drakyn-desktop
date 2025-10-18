"""
Agent orchestrator - core reasoning loop with tool execution.
Simple, transparent, and easy to modify.
"""
import json
import logging
from typing import AsyncGenerator, List, Optional, Dict, Any
import httpx
from .models import (
    Message,
    ToolCall,
    ToolDefinition,
    AgentStep,
    AgentConfig,
    CompletionConfig
)
from .prompts import get_system_prompt_with_tools

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Orchestrates agent reasoning loop with tool execution.

    Uses a simple iterative approach:
    1. Get model response
    2. Check for tool calls
    3. Execute tools if needed
    4. Loop until final answer

    Designed to be easy to understand and modify.
    """

    def __init__(
        self,
        model: str,
        tools: List[ToolDefinition],
        config: Optional[AgentConfig] = None,
        mcp_url: str = "http://localhost:8001"
    ):
        """
        Initialize agent orchestrator.

        Args:
            model: Model identifier (e.g., "openai/gpt-4" or "vllm/local-model")
            tools: List of available tools
            config: Agent configuration
            mcp_url: URL of MCP server for tool execution
        """
        self.model = model
        self.tools = tools
        self.config = config or AgentConfig()
        self.mcp_url = mcp_url
        self.system_prompt = (
            self.config.system_prompt or
            get_system_prompt_with_tools(tools)
        )

    async def run(
        self,
        user_message: str,
        conversation_history: Optional[List[Message]] = None
    ) -> AsyncGenerator[AgentStep, None]:
        """
        Main agent loop - yields steps for streaming to UI.

        Args:
            user_message: User's input message
            conversation_history: Prior messages in conversation

        Yields:
            AgentStep: Each step of agent reasoning (thinking, tool calls, results, answer)
        """
        # Initialize conversation with system prompt and history
        messages = conversation_history or []

        # Add system prompt if not already present
        if not messages or messages[0].role != "system":
            messages.insert(0, Message(role="system", content=self.system_prompt))

        # Add user message
        messages.append(Message(role="user", content=user_message))

        # Main reasoning loop
        for iteration in range(self.config.max_iterations):
            if self.config.verbose:
                logger.info(f"Agent iteration {iteration + 1}/{self.config.max_iterations}")

            # Step 1: Get model response
            yield AgentStep(type="thinking", iteration=iteration)

            try:
                response_text = await self._get_model_response(messages)

                if self.config.verbose:
                    logger.debug(f"Model response: {response_text[:200]}...")

                # Step 2: Try to parse tool call
                tool_call = self._parse_tool_call(response_text)

                if tool_call:
                    # Model wants to use a tool
                    yield AgentStep(
                        type="tool_call",
                        iteration=iteration,
                        tool_name=tool_call.tool,
                        tool_args=tool_call.args,
                        content=tool_call.reasoning
                    )

                    # Step 3: Execute tool
                    try:
                        tool_result = await self._execute_tool(tool_call)

                        yield AgentStep(
                            type="tool_result",
                            iteration=iteration,
                            tool_name=tool_call.tool,
                            result=tool_result
                        )

                        # Add to conversation context
                        messages.append(Message(
                            role="assistant",
                            content=response_text,
                            tool_call=tool_call
                        ))
                        messages.append(Message(
                            role="tool",
                            name=tool_call.tool,
                            content=json.dumps(tool_result)
                        ))

                        # Continue to next iteration with tool result
                        continue

                    except Exception as e:
                        error_msg = f"Tool execution failed: {str(e)}"
                        logger.error(error_msg)

                        yield AgentStep(
                            type="error",
                            iteration=iteration,
                            tool_name=tool_call.tool,
                            error=error_msg
                        )

                        # Add error to context so model can recover
                        messages.append(Message(
                            role="tool",
                            name=tool_call.tool,
                            content=f"Error: {error_msg}"
                        ))
                        continue
                else:
                    # No tool call - this is the final answer
                    yield AgentStep(
                        type="answer",
                        iteration=iteration,
                        content=response_text
                    )

                    # Add final message to history
                    messages.append(Message(
                        role="assistant",
                        content=response_text
                    ))

                    # Done!
                    break

            except Exception as e:
                error_msg = f"Model call failed: {str(e)}"
                logger.error(error_msg)

                yield AgentStep(
                    type="error",
                    iteration=iteration,
                    error=error_msg
                )
                break

        # Return final conversation state
        return messages

    async def _get_model_response(self, messages: List[Message]) -> str:
        """
        Get response from LLM using LiteLLM.

        Args:
            messages: Conversation history

        Returns:
            Model's text response
        """
        from ..providers import LiteLLMClient

        # Initialize client based on model type
        if self.model.startswith("vllm/") or "localhost" in self.model:
            # Use local vLLM server
            from ..providers import vLLMClient
            client = vLLMClient()
            # Strip vllm/ prefix for actual model name
            model_name = self.model.replace("vllm/", "")
        else:
            # Use cloud provider (OpenAI, Anthropic, etc.)
            client = LiteLLMClient()
            model_name = self.model

        # Update config with actual model name
        config = CompletionConfig(
            model=model_name,
            temperature=self.config.completion_config.temperature,
            max_tokens=self.config.completion_config.max_tokens,
            top_p=self.config.completion_config.top_p,
            stream=False
        )

        # Convert tools to LiteLLM format (optional - for function calling support)
        tools_dict = [tool.to_dict() for tool in self.tools] if self.tools else None

        # Get completion
        response = await client.complete(
            messages=messages,
            config=config,
            tools=tools_dict
        )

        return response

    def _parse_tool_call(self, response: str) -> Optional[ToolCall]:
        """
        Parse tool call from model response.

        Looks for JSON object with structure:
        {
          "tool": "tool_name",
          "args": {...},
          "reasoning": "..."
        }

        Args:
            response: Raw model output

        Returns:
            ToolCall object if valid tool call found, None otherwise
        """
        try:
            # Try to find JSON in response
            # Look for { ... } pattern
            start = response.find('{')
            end = response.rfind('}')

            if start == -1 or end == -1:
                return None

            json_str = response[start:end + 1]
            data = json.loads(json_str)

            # Validate it's a tool call
            if "tool" in data and "args" in data:
                return ToolCall(
                    tool=data["tool"],
                    args=data.get("args", {}),
                    reasoning=data.get("reasoning")
                )

            return None

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            if self.config.verbose:
                logger.debug(f"Failed to parse tool call: {e}")
            return None

    async def _execute_tool(self, tool_call: ToolCall) -> Dict[str, Any]:
        """
        Execute tool via MCP server.

        Args:
            tool_call: Tool to execute

        Returns:
            Tool execution result

        Raises:
            Exception: If tool execution fails
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.mcp_url}/execute",
                json={
                    "tool": tool_call.tool,
                    "arguments": tool_call.args
                },
                timeout=30.0
            )
            response.raise_for_status()

            result = response.json()

            if result.get("error"):
                raise Exception(result["error"])

            return result.get("result", {})
