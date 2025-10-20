"""
System prompts for agent behavior.
Defines how the agent should think, reason, and use tools.
"""

AGENT_SYSTEM_PROMPT = """You are a helpful AI assistant.

## Core Rules

1. **For greetings and general questions**: Just answer directly. Be friendly and helpful.
2. **For file/system tasks**: Use tools only when the user explicitly asks you to search or read files.

## How to Respond

Most of the time, just respond normally to the user like a helpful assistant.

Only use a tool when the user specifically asks you to search for files or read files.

## Tool Format

When you need to use a tool, respond with ONLY this JSON format:

```json
{
  "tool": "tool_name",
  "args": {"parameter": "value"},
  "reasoning": "why"
}
```

Be conversational and helpful. Don't overthink it."""

TOOL_CALL_FORMAT_REMINDER = """
Remember to format tool calls as JSON:
{
  "tool": "tool_name",
  "args": {...},
  "reasoning": "why you're calling this tool"
}
"""


def get_system_prompt_with_tools(tools: list) -> str:
    """
    Generate system prompt with available tools listed.

    Args:
        tools: List of ToolDefinition objects

    Returns:
        Complete system prompt including tool descriptions
    """
    if not tools:
        return AGENT_SYSTEM_PROMPT

    tools_section = "\n## Available Tools\n\n"
    for tool in tools:
        tools_section += f"### {tool.name}\n"
        tools_section += f"{tool.description}\n\n"
        tools_section += "**Parameters:**\n```json\n"
        tools_section += str(tool.parameters)
        tools_section += "\n```\n\n"

    return AGENT_SYSTEM_PROMPT + "\n" + tools_section
