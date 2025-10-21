"""
Pydantic models for agent orchestration.
Provides type-safe schemas for messages, tool calls, and agent steps.
"""
from typing import Optional, Dict, Any, List, Literal
from pydantic import BaseModel, Field


class Message(BaseModel):
    """A message in the conversation."""
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    tool_call: Optional["ToolCall"] = None
    tool_result: Optional[Dict[str, Any]] = None
    name: Optional[str] = None  # Tool name for tool messages
    tool_call_id: Optional[str] = None  # Tool call ID for Anthropic (required for tool role messages)


class ToolCall(BaseModel):
    """A structured tool call parsed from model output."""
    tool: str = Field(..., description="Name of the tool to call")
    args: Dict[str, Any] = Field(default_factory=dict, description="Arguments for the tool")
    reasoning: Optional[str] = Field(None, description="Model's reasoning for calling this tool")


class ToolDefinition(BaseModel):
    """Schema for defining a tool's interface."""
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON schema for tool parameters

    def to_dict(self) -> Dict[str, Any]:
        """Convert to format expected by LLM APIs."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }


class AgentStep(BaseModel):
    """A single step in the agent's reasoning process."""
    type: Literal["thinking", "tool_call", "tool_result", "answer", "error"]
    iteration: Optional[int] = None
    content: Optional[str] = None
    tool_name: Optional[str] = None
    tool_args: Optional[Dict[str, Any]] = None
    result: Optional[Any] = None
    error: Optional[str] = None

    def to_stream_dict(self) -> Dict[str, Any]:
        """Convert to format for streaming to UI."""
        return {
            "type": self.type,
            "iteration": self.iteration,
            "content": self.content,
            "tool_name": self.tool_name,
            "tool_args": self.tool_args,
            "result": self.result,
            "error": self.error
        }


class CompletionConfig(BaseModel):
    """Configuration for LLM completion calls."""
    model: str = "openai/gpt-4"
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(512, gt=0)  # Reduced from 2048 to prevent rambling
    top_p: float = Field(0.9, ge=0.0, le=1.0)
    stop: Optional[List[str]] = None
    stream: bool = True


class AgentConfig(BaseModel):
    """Configuration for agent orchestrator."""
    max_iterations: int = Field(5, gt=0, le=20)
    completion_config: CompletionConfig = Field(default_factory=CompletionConfig)
    system_prompt: Optional[str] = None
    verbose: bool = False
