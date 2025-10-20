"""
MCP (Model Context Protocol) server for agent tool integration.
"""
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn

# Import tools
from tools.files import FileSearchTool
from tools.gmail import GmailTool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Drakyn MCP Server")

# Add CORS middleware for Electron app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tool registry
AVAILABLE_TOOLS = {
    "search_files": FileSearchTool,
    "gmail": GmailTool,
}


class Tool(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]


class ToolCall(BaseModel):
    tool: str
    arguments: Dict[str, Any]


class ToolResponse(BaseModel):
    result: Any
    error: Optional[str] = None


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "mcp",
        "tools_available": len(AVAILABLE_TOOLS)
    }


@app.get("/tools", response_model=List[Tool])
async def list_tools():
    """List available tools."""
    tools = []
    for name, tool_class in AVAILABLE_TOOLS.items():
        tools.append(Tool(
            name=tool_class.name,
            description=tool_class.description,
            parameters=tool_class.get_schema()
        ))
    return tools


@app.post("/execute", response_model=ToolResponse)
async def execute_tool(call: ToolCall):
    """Execute a tool with given arguments."""
    try:
        logger.info(f"Executing tool: {call.tool} with args: {call.arguments}")

        # Find tool in registry
        if call.tool not in AVAILABLE_TOOLS:
            raise HTTPException(
                status_code=404,
                detail=f"Tool '{call.tool}' not found. Available tools: {list(AVAILABLE_TOOLS.keys())}"
            )

        tool_class = AVAILABLE_TOOLS[call.tool]

        # Execute tool
        result = await tool_class.execute(call.arguments)

        logger.info(f"Tool execution completed: {call.tool}")

        return ToolResponse(
            result=result,
            error=result.get("error") if isinstance(result, dict) else None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Tool execution failed: {str(e)}")
        return ToolResponse(
            result=None,
            error=str(e)
        )


if __name__ == "__main__":
    logger.info(f"Starting MCP Server with {len(AVAILABLE_TOOLS)} tools")
    logger.info(f"Available tools: {list(AVAILABLE_TOOLS.keys())}")
    uvicorn.run(app, host="127.0.0.1", port=8001)
