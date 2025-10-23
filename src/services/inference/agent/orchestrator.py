"""
Agent orchestrator - core reasoning loop with tool execution.
Simple, transparent, and easy to modify.
"""
import json
import logging
import time
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
from providers import LiteLLMClient, vLLMClient, OllamaClient

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
        mcp_url: str = "http://localhost:8001",
        project_context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize agent orchestrator.

        Args:
            model: Model identifier (e.g., "openai/gpt-4" or "vllm/local-model")
            tools: List of available tools
            config: Agent configuration
            mcp_url: URL of MCP server for tool execution
            project_context: Optional dict with current project info (id, name, summary, status)
        """
        self.model = model
        self.tools = tools
        self.config = config or AgentConfig()
        self.mcp_url = mcp_url
        self.project_context = project_context
        self.system_prompt = (
            self.config.system_prompt or
            get_system_prompt_with_tools(tools, project_context)
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
        logger.info(f"[AGENT] Starting agent run with user message: {user_message[:100]}...")

        # Add system prompt if not already present
        if not messages or messages[0].role != "system":
            messages.insert(0, Message(role="system", content=self.system_prompt))
            logger.info(f"[AGENT] Added system prompt ({len(self.system_prompt)} chars)")

        # Add user message
        messages.append(Message(role="user", content=user_message))
        logger.info(f"[AGENT] Initial context has {len(messages)} messages")

        # Main reasoning loop
        logger.info(f"[AGENT] Starting reasoning loop (max {self.config.max_iterations} iterations)")
        for iteration in range(self.config.max_iterations):
            logger.info(f"[AGENT] ========== Iteration {iteration + 1}/{self.config.max_iterations} ==========")
            logger.info(f"[AGENT] Current context: {len(messages)} messages")

            # Log the last few messages for context
            if len(messages) > 1:
                recent_msgs = messages[-3:] if len(messages) > 3 else messages[1:]  # Skip system prompt
                for i, msg in enumerate(recent_msgs):
                    content_preview = msg.content[:100] if msg.content else "<no content>"
                    logger.info(f"[AGENT]   Message {len(messages) - len(recent_msgs) + i}: {msg.role} - {content_preview}...")

            # Step 1: Get model response
            yield AgentStep(type="thinking", iteration=iteration)

            try:
                import time
                start_get_response = time.time()
                logger.info(f"Starting _get_model_response at {time.strftime('%H:%M:%S')}")

                response_text = await self._get_model_response(messages)

                elapsed_get_response = time.time() - start_get_response
                logger.info(f"_get_model_response completed in {elapsed_get_response:.2f}s")

                # Always log the full model response for debugging
                if not response_text or not response_text.strip():
                    logger.warning(f"[AGENT] Model returned EMPTY response! Length: {len(response_text)}, repr: {repr(response_text)}")
                else:
                    logger.info(f"Model response (iteration {iteration}): {response_text[:500]}...")

                if self.config.verbose:
                    logger.debug(f"Full model response: {response_text}")

                # Step 2: Try to parse tool call
                tool_call = self._parse_tool_call(response_text)

                if tool_call:
                    # Model wants to use a tool
                    logger.info(f"Tool call detected: {tool_call.tool} with args: {tool_call.args}")
                    yield AgentStep(
                        type="tool_call",
                        iteration=iteration,
                        tool_name=tool_call.tool,
                        tool_args=tool_call.args,
                        content=tool_call.reasoning
                    )

                    # Step 3: Execute tool
                    try:
                        logger.info(f"[AGENT] Executing tool: {tool_call.tool}")
                        tool_result = await self._execute_tool(tool_call)
                        logger.info(f"[AGENT] Tool result: {json.dumps(tool_result, indent=2)[:500]}...")

                        # Check if this is a setup_required response
                        if isinstance(tool_result, dict) and tool_result.get("setup_required"):
                            logger.info(f"[AGENT] Tool requires setup - agent should guide user")

                        yield AgentStep(
                            type="tool_result",
                            iteration=iteration,
                            tool_name=tool_call.tool,
                            result=tool_result
                        )

                        # Add to conversation context
                        # Generate unique tool call ID for Anthropic
                        import uuid
                        tool_call_id = f"toolu_{uuid.uuid4().hex[:24]}"

                        assistant_msg = Message(
                            role="assistant",
                            content=response_text,
                            tool_call=tool_call
                        )
                        tool_msg = Message(
                            role="tool",
                            name=tool_call.tool,
                            content=json.dumps(tool_result),
                            tool_call_id=tool_call_id
                        )
                        messages.append(assistant_msg)
                        messages.append(tool_msg)

                        logger.info(f"[AGENT] Added tool call and result to context. Context now has {len(messages)} messages")

                        # Continue to next iteration with tool result
                        continue

                    except Exception as e:
                        error_msg = f"Tool execution failed: {str(e)}"
                        logger.error(f"[AGENT] {error_msg}")
                        logger.error(f"[AGENT] Exception type: {type(e).__name__}")

                        yield AgentStep(
                            type="error",
                            iteration=iteration,
                            tool_name=tool_call.tool,
                            error=error_msg
                        )

                        # Add error to context so model can recover
                        error_msg_obj = Message(
                            role="tool",
                            name=tool_call.tool,
                            content=f"Error: {error_msg}"
                        )
                        messages.append(error_msg_obj)
                        logger.info(f"[AGENT] Added error to context. Context now has {len(messages)} messages")
                        continue
                else:
                    # No tool call - this is the final answer
                    logger.info(f"[AGENT] Direct answer (no tool call): {response_text[:200]}...")

                    # Clean up response - remove common formatting artifacts
                    cleaned_response = response_text.strip()
                    # Remove role prefixes like "### Assistant:", "Assistant:", etc.
                    import re
                    cleaned_response = re.sub(r'^#{0,3}\s*(?:Assistant|User|System):\s*', '', cleaned_response, flags=re.IGNORECASE | re.MULTILINE)
                    cleaned_response = cleaned_response.strip()

                    logger.info(f"[AGENT] Cleaned response: {cleaned_response[:200]}...")

                    # Handle empty responses
                    if not cleaned_response:
                        logger.error(f"[AGENT] Model returned empty response after cleaning. This is a model capability issue.")
                        error_message = (
                            "I apologize, but I'm having trouble processing your request. "
                            "The model I'm using (gpt-oss:20b) may not be suitable for this task. "
                            "Please try:\n"
                            "1. Using a different model in the Settings page\n"
                            "2. Rephrasing your question\n"
                            "3. Asking a simpler question"
                        )
                        yield AgentStep(
                            type="error",
                            iteration=iteration,
                            error=error_message
                        )
                        break

                    yield AgentStep(
                        type="answer",
                        iteration=iteration,
                        content=cleaned_response
                    )

                    # Add final message to history
                    final_msg = Message(
                        role="assistant",
                        content=response_text
                    )
                    messages.append(final_msg)
                    logger.info(f"[AGENT] Added final answer to context. Context now has {len(messages)} messages")

                    # Done!
                    logger.info(f"[AGENT] Agent completed successfully after {iteration + 1} iteration(s)")
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

        # Note: Conversation state is maintained in messages list
        # Async generators cannot return values, only yield

    async def _get_model_response(self, messages: List[Message]) -> str:
        """
        Get response from LLM using LiteLLM.

        Args:
            messages: Conversation history

        Returns:
            Model's text response
        """
        start = time.time()
        logger.info(f"[TIMING] Entered _get_model_response")

        # Initialize client based on model type
        if self.model.startswith("vllm/"):
            # Use local vLLM server
            client = vLLMClient()
            # Strip vllm/ prefix for actual model name
            model_name = self.model.replace("vllm/", "")
        elif self.model.startswith("ollama/"):
            # Use Ollama server
            client = OllamaClient()
            # Strip ollama/ prefix for actual model name
            model_name = self.model.replace("ollama/", "")
        else:
            # Use cloud provider (OpenAI, Anthropic, etc.) or auto-detect
            client = LiteLLMClient()
            model_name = self.model

        logger.info(f"[TIMING] Client initialized in {time.time() - start:.3f}s")

        # Update config with actual model name
        config = CompletionConfig(
            model=model_name,
            temperature=self.config.completion_config.temperature,
            max_tokens=self.config.completion_config.max_tokens,
            top_p=self.config.completion_config.top_p,
            stream=False
        )

        logger.info(f"[TIMING] Config created in {time.time() - start:.3f}s")

        # Convert tools to LiteLLM format (optional - for function calling support)
        tools_dict = [tool.to_dict() for tool in self.tools] if self.tools else None

        logger.info(f"[TIMING] Tools prepared in {time.time() - start:.3f}s, calling client.complete()")

        # Get completion
        response = await client.complete(
            messages=messages,
            config=config,
            tools=tools_dict
        )

        logger.info(f"[TIMING] Total _get_model_response time: {time.time() - start:.3f}s")
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
        logger.info(f"[MCP] Calling MCP server at {self.mcp_url}/execute")
        logger.info(f"[MCP] Tool: {tool_call.tool}, Args: {json.dumps(tool_call.args)}")

        async with httpx.AsyncClient() as client:
            start = time.time()
            response = await client.post(
                f"{self.mcp_url}/execute",
                json={
                    "tool": tool_call.tool,
                    "arguments": tool_call.args
                },
                timeout=30.0
            )
            elapsed = time.time() - start
            logger.info(f"[MCP] HTTP request completed in {elapsed:.3f}s, status: {response.status_code}")

            response.raise_for_status()

            result = response.json()
            logger.info(f"[MCP] Raw response from MCP: {json.dumps(result, indent=2)[:500]}...")

            # Extract the actual tool result
            tool_result = result.get("result", {})

            # If there's an error but it's a setup_required error, return the full result
            # so the agent can guide the user through setup
            if result.get("error"):
                logger.warning(f"[MCP] Tool returned error: {result.get('error')}")
                # Check if this is a setup_required error
                if isinstance(tool_result, dict) and tool_result.get("setup_required"):
                    logger.info(f"[MCP] This is a setup_required error - returning full result to agent")
                    logger.info(f"[MCP] Setup instructions included: {bool(tool_result.get('instructions'))}")
                    # Return the full result with setup instructions
                    return tool_result
                else:
                    # Regular error - raise exception
                    logger.error(f"[MCP] Regular error - raising exception")
                    raise Exception(result["error"])

            logger.info(f"[MCP] Returning successful result")
            return tool_result
