"""
Agent module for Drakyn Desktop.
Provides simple, transparent orchestration for LLM agents with tool use.
"""
from .models import (
    Message,
    ToolCall,
    ToolDefinition,
    AgentStep,
    CompletionConfig,
    AgentConfig
)
from .prompts import (
    AGENT_SYSTEM_PROMPT,
    get_system_prompt_with_tools
)

__all__ = [
    "Message",
    "ToolCall",
    "ToolDefinition",
    "AgentStep",
    "CompletionConfig",
    "AgentConfig",
    "AGENT_SYSTEM_PROMPT",
    "get_system_prompt_with_tools",
]
