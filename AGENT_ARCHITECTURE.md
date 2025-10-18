# Agent Architecture Documentation

## Overview

Drakyn Desktop uses a **hybrid agent architecture** that combines custom orchestration with battle-tested off-the-shelf components. This design prioritizes speed, debuggability, and ease of modification by coding agents.

## Design Philosophy

- **Simple over complex**: Linear reasoning loop instead of graph-based abstractions
- **Transparent**: Every step is visible and debuggable
- **Modular**: Small focused files (~100-250 lines each)
- **Extensible**: Add tools by implementing a simple class interface
- **Multi-provider**: Switch between local vLLM and cloud providers seamlessly

## Architecture Components

### 1. Agent Orchestrator
**Location**: `src/services/inference/agent/orchestrator.py` (285 lines)

The core reasoning loop that:
- Manages conversation context
- Calls LLM for responses
- Parses tool calls from model outputs
- Executes tools via MCP HTTP calls
- Handles errors and retries
- Streams steps to UI in real-time

**Flow**:
```
User message → Add to context → Loop (max 5 iterations):
  ├─ Get model response via LiteLLM
  ├─ Parse for tool call (JSON extraction)
  ├─ If tool call found:
  │   ├─ Execute via MCP server POST /execute
  │   ├─ Add result to context
  │   └─ Continue to next iteration
  └─ If no tool call:
      └─ Return final answer
```

### 2. LLM Provider Layer
**Location**: `src/services/inference/providers/litellm_client.py` (117 lines)

Abstraction over multiple LLM providers using [LiteLLM](https://github.com/BerriAI/litellm):

- **LiteLLMClient**: Unified interface for all providers
- **vLLMClient**: Pre-configured for local GPU inference
- Supports: vLLM, OpenAI, Anthropic, Cohere, and 100+ others

**Usage**:
```python
# Local vLLM
client = vLLMClient()
response = await client.complete(messages, config)

# Cloud provider
client = LiteLLMClient()
response = await client.complete(messages, config)
```

### 3. Type-Safe Models
**Location**: `src/services/inference/agent/models.py` (89 lines)

Pydantic schemas for:
- `Message`: Conversation messages (user/assistant/tool/system)
- `ToolCall`: Structured tool invocations
- `ToolDefinition`: Tool interface schemas
- `AgentStep`: Streaming step objects (thinking/tool_call/tool_result/answer/error)
- `AgentConfig`: Orchestrator configuration

### 4. System Prompts
**Location**: `src/services/inference/agent/prompts.py` (77 lines)

Defines agent behavior:
- How to use tools (JSON format required)
- When to call tools vs respond directly
- Error handling guidelines
- Response style (concise, natural)

### 5. MCP Tool Server
**Location**: `src/services/mcp/server.py` (112 lines)

FastAPI server exposing tool execution API:
- **GET /tools**: List available tools with schemas
- **POST /execute**: Execute a tool with arguments
- **GET /health**: Health check

Tool registry pattern:
```python
AVAILABLE_TOOLS = {
    "search_files": FileSearchTool,
    # Add more tools here
}
```

### 6. Tool Implementations
**Location**: `src/services/mcp/tools/`

Each tool is a class with:
- `name`: Tool identifier
- `description`: What the tool does
- `get_schema()`: JSON schema for parameters
- `execute(args)`: Async execution function

**Example Tool**: `files.py` (131 lines)
- Search files by pattern (supports wildcards)
- Recursive directory traversal
- Safe path handling
- Returns file metadata (path, size, modified date)

## Communication Flow

### Complete Example: "Find all Python files in my Documents"

```
1. USER INPUT
   User types message in Electron UI

2. UI (app.js)
   POST /v1/agent/chat {message: "Find all Python files..."}
   Opens SSE stream

3. INFERENCE SERVER (server.py)
   - Fetches tools from MCP server
   - Creates AgentOrchestrator instance
   - Starts iteration loop

4. ITERATION 1: REASONING
   - LiteLLMClient calls vLLM with system prompt + tools schema
   - Model thinks: "I need to use search_files tool"
   - Streams: {"type": "thinking", "iteration": 0}

5. TOOL CALL PARSING
   - Orchestrator finds JSON in response:
     {
       "tool": "search_files",
       "args": {"pattern": "*.py", "directory": "~/Documents"},
       "reasoning": "Search for Python files"
     }
   - Streams: {"type": "tool_call", "tool_name": "search_files", ...}

6. TOOL EXECUTION
   - Orchestrator POSTs to http://localhost:8001/execute
   - MCP server routes to FileSearchTool.execute()
   - Tool searches filesystem, returns file list
   - Streams: {"type": "tool_result", "result": [...]}

7. ITERATION 2: FINAL ANSWER
   - Context now includes tool results
   - LiteLLMClient calls vLLM again
   - Model formats response: "I found 42 Python files..."
   - No tool call detected
   - Streams: {"type": "answer", "content": "I found..."}

8. UI UPDATES
   - Shows "Thinking..." during iteration 1
   - Shows "Calling tool: search_files" with args
   - Shows "Tool result received"
   - Shows final answer
   - Re-enables input
```

## Streaming Protocol

The agent uses **Server-Sent Events (SSE)** to stream steps:

```
data: {"type": "thinking", "iteration": 0}

data: {"type": "tool_call", "tool_name": "search_files", "tool_args": {...}}

data: {"type": "tool_result", "tool_name": "search_files", "result": [...]}

data: {"type": "answer", "content": "I found 42 Python files..."}

data: {"type": "done"}
```

UI reads stream and updates in real-time, showing agent's reasoning process.

## Adding New Tools

### Step 1: Create Tool Class

```python
# src/services/mcp/tools/my_tool.py

from typing import Dict, Any
from pydantic import BaseModel, Field

class MyToolArgs(BaseModel):
    param1: str = Field(..., description="First parameter")
    param2: int = Field(default=10, description="Second parameter")

class MyTool:
    name = "my_tool"
    description = "Description of what this tool does"

    @staticmethod
    def get_schema() -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "param1": {"type": "string", "description": "..."},
                "param2": {"type": "integer", "default": 10}
            },
            "required": ["param1"]
        }

    @staticmethod
    async def execute(args: Dict[str, Any]) -> Dict[str, Any]:
        validated = MyToolArgs(**args)

        # Do the work
        result = do_something(validated.param1, validated.param2)

        return {
            "result": result,
            "status": "success"
        }
```

### Step 2: Register Tool

```python
# src/services/mcp/server.py

from tools.my_tool import MyTool

AVAILABLE_TOOLS = {
    "search_files": FileSearchTool,
    "my_tool": MyTool,  # Add here
}
```

### Step 3: Test

Restart MCP server, tool is now available to the agent automatically!

## Configuration

### Agent Settings

```python
# In server.py when creating AgentOrchestrator

config = AgentConfig(
    max_iterations=5,  # Max tool use rounds
    completion_config=CompletionConfig(
        temperature=0.7,  # Creativity (0-1)
        max_tokens=2048,  # Response length limit
        top_p=0.9         # Nucleus sampling
    ),
    verbose=True  # Log every step
)
```

### Model Selection

```python
# Use local vLLM model
agent = AgentOrchestrator(
    model="vllm/Qwen/Qwen2.5-0.5B-Instruct",
    tools=tools
)

# Use OpenAI
agent = AgentOrchestrator(
    model="openai/gpt-4",
    tools=tools
)

# Use Anthropic
agent = AgentOrchestrator(
    model="anthropic/claude-3-5-sonnet-20241022",
    tools=tools
)
```

## File Structure

```
src/services/
├── inference/
│   ├── server.py              # FastAPI app (345 lines)
│   │   └─ /v1/agent/chat      # Agent endpoint with SSE
│   ├── agent/
│   │   ├── orchestrator.py    # Core loop (285 lines)
│   │   ├── models.py          # Pydantic schemas (89 lines)
│   │   └── prompts.py         # System prompts (77 lines)
│   ├── providers/
│   │   └── litellm_client.py  # LLM wrapper (117 lines)
│   └── requirements.txt       # Python deps
└── mcp/
    ├── server.py              # Tool execution API (112 lines)
    ├── tools/
    │   ├── files.py           # File search (131 lines)
    │   └── ...                # More tools here
    └── requirements.txt
```

**Total: ~1,200 lines across focused modules**

Each file is small enough to fit in a coding agent's context window.

## Dependencies

### Inference Server
```
fastapi>=0.109.0      # Web framework
uvicorn>=0.27.0       # ASGI server
vllm>=0.3.0           # Local GPU inference
torch>=2.1.0          # PyTorch
pydantic>=2.5.0       # Type validation
litellm>=1.0.0        # Multi-provider LLM
instructor>=1.0.0     # Structured outputs (reserved)
httpx>=0.24.0         # Async HTTP client
```

### MCP Server
```
fastapi>=0.109.0
uvicorn>=0.27.0
pydantic>=2.5.0
```

## Debugging

### Enable Verbose Logging

```python
config = AgentConfig(verbose=True)
```

Logs every:
- Model call
- Tool call parsed
- Tool execution
- Error encountered

### Check MCP Server Health

```bash
curl http://localhost:8001/health
curl http://localhost:8001/tools
```

### Test Tool Execution Directly

```bash
curl -X POST http://localhost:8001/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "search_files",
    "arguments": {"pattern": "*.py", "directory": "~"}
  }'
```

### Inspect SSE Stream

```bash
curl -N -X POST http://localhost:8000/v1/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Find Python files", "stream": true}'
```

## Performance

- **Local vLLM**: ~2-5 sec per iteration (model dependent)
- **Cloud APIs**: ~1-3 sec per iteration
- **Tool execution**: 10ms - 5sec (tool dependent)
- **Streaming**: Real-time, 0 latency to first token

## Future Enhancements

1. **Conversation Memory**: Persist chat history to SQLite
2. **More Tools**:
   - Email (IMAP/Gmail API)
   - Code execution (sandboxed Python)
   - Web search (SerpAPI/Tavily)
   - Calendar (Google Calendar)
   - Database queries
3. **Streaming Optimization**: Token-level streaming instead of step-level
4. **Function Calling**: Native support in models (GPT-4, Claude)
5. **Multi-Agent**: Specialized agents for different tasks
6. **Human-in-Loop**: Approval prompts for sensitive operations

## References

- [LiteLLM Documentation](https://docs.litellm.ai/)
- [FastAPI Streaming](https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse)
- [Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- [Pydantic Models](https://docs.pydantic.dev/)
