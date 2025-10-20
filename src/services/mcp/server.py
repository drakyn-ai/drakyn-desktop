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


@app.get("/credentials/{tool_name}/status")
async def get_credential_status(tool_name: str):
    """Check if credentials are configured for a tool."""
    if tool_name not in AVAILABLE_TOOLS:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

    tool_class = AVAILABLE_TOOLS[tool_name]

    # Check if tool has credential checking capability
    if hasattr(tool_class, 'is_configured'):
        is_configured = tool_class.is_configured()
        setup_instructions = tool_class.get_setup_instructions() if hasattr(tool_class, 'get_setup_instructions') else None

        return {
            "tool": tool_name,
            "configured": is_configured,
            "setup_instructions": setup_instructions
        }

    # Tool doesn't require credentials
    return {
        "tool": tool_name,
        "configured": True,
        "requires_credentials": False
    }


class CredentialUpload(BaseModel):
    tool_name: str
    credentials: str  # JSON string of credentials file


@app.post("/credentials/upload")
async def upload_credentials(upload: CredentialUpload):
    """Upload credentials for a tool."""
    import json
    from pathlib import Path

    try:
        # Validate tool exists
        if upload.tool_name not in AVAILABLE_TOOLS:
            raise HTTPException(status_code=404, detail=f"Tool '{upload.tool_name}' not found")

        # Validate JSON
        try:
            credentials_data = json.loads(upload.credentials)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON in credentials")

        # Save credentials based on tool
        if upload.tool_name == "gmail":
            credentials_dir = Path(__file__).parent / "credentials"
            credentials_dir.mkdir(exist_ok=True)
            credentials_path = credentials_dir / "gmail_credentials.json"

            with open(credentials_path, 'w') as f:
                json.dump(credentials_data, f, indent=2)

            logger.info(f"Gmail credentials saved successfully")

            return {
                "success": True,
                "message": "Gmail credentials saved successfully",
                "next_step": "You can now use Gmail commands"
            }

        else:
            raise HTTPException(status_code=400, detail=f"Credential upload not supported for '{upload.tool_name}'")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Credential upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    logger.info(f"Starting MCP Server with {len(AVAILABLE_TOOLS)} tools")
    logger.info(f"Available tools: {list(AVAILABLE_TOOLS.keys())}")
    uvicorn.run(app, host="127.0.0.1", port=8001)
