"""
Inference server for running LLM models locally.
Supports vLLM, SGLang, and other backends via abstraction layer.
"""
import asyncio
import logging
import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Add current directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, AsyncGenerator
import uvicorn
import httpx

# Load environment variables FIRST before importing vLLM
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

# Setup logging to both console and file
from logging.handlers import RotatingFileHandler

# Create logs directory
logs_dir = Path(__file__).parent / 'logs'
logs_dir.mkdir(exist_ok=True)

# Configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter(
    '%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

# Console handler (stdout)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
root_logger.addHandler(console_handler)

# File handler with rotation (10MB max, keep 5 backups)
file_handler = RotatingFileHandler(
    logs_dir / 'inference_server.log',
    maxBytes=10 * 1024 * 1024,  # 10MB
    backupCount=5,
    encoding='utf-8'
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)
root_logger.addHandler(file_handler)

logger = logging.getLogger(__name__)
logger.info(f"Logging to console and {logs_dir / 'inference_server.log'}")

# Configuration
INFERENCE_ENGINE = os.getenv("INFERENCE_ENGINE", "vllm")
OPENAI_COMPATIBLE_URL = os.getenv("OPENAI_COMPATIBLE_URL", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "Qwen/Qwen2.5-0.5B-Instruct")
CURRENT_MODEL = os.getenv("CURRENT_MODEL")  # Previously selected model (persisted)
AUTO_LOAD_MODEL = os.getenv("AUTO_LOAD_MODEL", "true").lower() == "true"
GPU_MEMORY_UTILIZATION = float(os.getenv("GPU_MEMORY_UTILIZATION", "0.9"))

# Conditionally import vLLM only when needed
if INFERENCE_ENGINE == "vllm":
    logger.info("Importing vLLM for local inference...")
    try:
        from vllm import LLM, SamplingParams
        from vllm.outputs import RequestOutput
        logger.info("vLLM imported successfully")
    except ImportError as e:
        logger.error(f"Failed to import vLLM: {e}")
        logger.info("Falling back to OpenAI-compatible mode")
        INFERENCE_ENGINE = "openai_compatible"
else:
    logger.info(f"Using OpenAI-compatible server at {OPENAI_COMPATIBLE_URL}")
    # Create dummy classes so the type hints don't fail
    LLM = None
    SamplingParams = None
    RequestOutput = None

# Import agent components
from agent.orchestrator import AgentOrchestrator
from agent.models import AgentConfig, Message, ToolDefinition

logger.info(f"Loaded config from {env_path}")
logger.info(f"Inference engine: {INFERENCE_ENGINE}")

app = FastAPI(title="Drakyn Inference Server")

# Add CORS middleware for Electron app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state for loaded models
loaded_models: Dict[str, any] = {}  # Can hold LLM objects or None
current_model: Optional[str] = None
startup_complete: bool = False
openai_client: Optional[httpx.AsyncClient] = None

class CompletionRequest(BaseModel):
    prompt: str
    max_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.9
    stop: Optional[List[str]] = None
    stream: bool = False

class CompletionResponse(BaseModel):
    text: str
    model: str
    finish_reason: str

class LoadModelRequest(BaseModel):
    model_name_or_path: str
    gpu_memory_utilization: float = 0.9
    tensor_parallel_size: int = 1
    max_model_len: Optional[int] = None

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "inference",
        "inference_engine": INFERENCE_ENGINE,
        "openai_compatible_url": OPENAI_COMPATIBLE_URL if INFERENCE_ENGINE == "openai_compatible" else None,
        "current_model": current_model,
        "loaded_models": list(loaded_models.keys())
    }

@app.get("/models")
async def list_models():
    """List currently loaded models."""
    return {
        "models": [
            {"name": name, "active": name == current_model}
            for name in loaded_models.keys()
        ],
        "current_model": current_model
    }

@app.get("/available_models")
async def list_available_models():
    """List models available on the external OpenAI-compatible server (for openai_compatible mode)."""
    global openai_client

    if INFERENCE_ENGINE != "openai_compatible":
        return {"models": [], "message": "Only available in openai_compatible mode"}

    try:
        # Initialize client if needed
        if not openai_client:
            openai_client = httpx.AsyncClient(base_url=OPENAI_COMPATIBLE_URL, timeout=60.0)

        # Fetch models from external server
        response = await openai_client.get("/v1/models")

        if response.status_code == 200:
            data = response.json()
            models = data.get('data', [])
            model_list = [{"id": m.get('id', m.get('name', 'unknown')), "name": m.get('id', m.get('name', 'unknown'))} for m in models]

            return {
                "models": model_list,
                "count": len(model_list),
                "source": OPENAI_COMPATIBLE_URL
            }
        else:
            raise HTTPException(status_code=500, detail=f"External server returned {response.status_code}")

    except httpx.ConnectError as e:
        raise HTTPException(status_code=503, detail=f"Cannot connect to {OPENAI_COMPATIBLE_URL}: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to list available models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class UpdateConfigRequest(BaseModel):
    inference_engine: str
    openai_compatible_url: str

@app.post("/update_config")
async def update_config(request: UpdateConfigRequest):
    """Update the .env configuration file."""
    try:
        env_path = Path(__file__).parent / '.env'

        # Read current .env file
        if env_path.exists():
            with open(env_path, 'r') as f:
                lines = f.readlines()

            # Update the relevant lines
            new_lines = []
            engine_updated = False
            url_updated = False

            for line in lines:
                if line.startswith('INFERENCE_ENGINE='):
                    new_lines.append(f'INFERENCE_ENGINE={request.inference_engine}\n')
                    engine_updated = True
                elif line.startswith('OPENAI_COMPATIBLE_URL='):
                    new_lines.append(f'OPENAI_COMPATIBLE_URL={request.openai_compatible_url}\n')
                    url_updated = True
                else:
                    new_lines.append(line)

            # Add lines if they didn't exist
            if not engine_updated:
                new_lines.insert(0, f'INFERENCE_ENGINE={request.inference_engine}\n')
            if not url_updated:
                new_lines.insert(1, f'OPENAI_COMPATIBLE_URL={request.openai_compatible_url}\n')

            # Write back to file
            with open(env_path, 'w') as f:
                f.writelines(new_lines)

            logger.info(f"Updated configuration: engine={request.inference_engine}, url={request.openai_compatible_url}")
            return {
                "status": "success",
                "message": "Configuration updated. Please restart the application."
            }
        else:
            raise HTTPException(status_code=404, detail=".env file not found")

    except Exception as e:
        logger.error(f"Failed to update config: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update config: {str(e)}")

def save_model_to_env(model_name: str):
    """Save the current model to .env file for persistence across restarts."""
    try:
        env_path = Path(__file__).parent / '.env'

        if env_path.exists():
            with open(env_path, 'r') as f:
                lines = f.readlines()

            # Update or add CURRENT_MODEL line
            model_updated = False
            new_lines = []

            for line in lines:
                if line.startswith('CURRENT_MODEL='):
                    new_lines.append(f'CURRENT_MODEL={model_name}\n')
                    model_updated = True
                else:
                    new_lines.append(line)

            # Add CURRENT_MODEL if it didn't exist
            if not model_updated:
                new_lines.append(f'CURRENT_MODEL={model_name}\n')

            with open(env_path, 'w') as f:
                f.writelines(new_lines)

            logger.info(f"Saved model '{model_name}' to .env for persistence")
    except Exception as e:
        logger.error(f"Failed to save model to .env: {e}")

@app.post("/load_model")
async def load_model(request: LoadModelRequest):
    """Load a model into memory using the configured inference engine."""
    global current_model, openai_client

    try:
        logger.info(f"Loading model: {request.model_name_or_path} (engine: {INFERENCE_ENGINE})")

        if INFERENCE_ENGINE == "vllm":
            # Check if model is already loaded
            if request.model_name_or_path in loaded_models:
                current_model = request.model_name_or_path
                logger.info(f"Model already loaded, switching to: {current_model}")
                return {
                    "status": "success",
                    "model": request.model_name_or_path,
                    "message": "Model already loaded"
                }

            # Initialize vLLM engine
            llm = LLM(
                model=request.model_name_or_path,
                gpu_memory_utilization=request.gpu_memory_utilization,
                tensor_parallel_size=request.tensor_parallel_size,
                max_model_len=request.max_model_len,
                trust_remote_code=True
            )

            loaded_models[request.model_name_or_path] = llm
            current_model = request.model_name_or_path

            # Save to .env for persistence
            save_model_to_env(current_model)

            logger.info(f"Successfully loaded model: {current_model}")
            return {
                "status": "success",
                "model": request.model_name_or_path,
                "message": "Model loaded successfully"
            }

        elif INFERENCE_ENGINE == "openai_compatible":
            # For OpenAI-compatible servers or cloud models, just set the model name
            current_model = request.model_name_or_path

            # Save to .env for persistence
            save_model_to_env(current_model)

            # Check if this is a cloud model
            is_cloud_model = any(current_model.startswith(prefix) for prefix in ['claude-', 'gpt-', 'anthropic/', 'openai/', 'gemini-'])

            if is_cloud_model:
                # Cloud model - no need to check Ollama server
                logger.info(f"Selected cloud model: {current_model}")
                return {
                    "status": "success",
                    "model": request.model_name_or_path,
                    "message": f"Cloud model '{request.model_name_or_path}' selected. Make sure API key is configured in Settings.",
                    "is_cloud": True
                }

            # For local Ollama models, test the connection
            # Initialize OpenAI client if not already done
            if not openai_client:
                openai_client = httpx.AsyncClient(base_url=OPENAI_COMPATIBLE_URL, timeout=60.0)

            # Test the connection by listing models
            try:
                logger.info(f"Testing connection to {OPENAI_COMPATIBLE_URL}...")
                response = await openai_client.get("/v1/models")

                if response.status_code == 200:
                    models_data = response.json()
                    available_models = [m.get('id', m.get('name', 'unknown')) for m in models_data.get('data', [])]

                    logger.info(f"Successfully connected! Found {len(available_models)} models")
                    logger.info(f"Available models: {', '.join(available_models[:5])}{'...' if len(available_models) > 5 else ''}")

                    # Check if requested model exists
                    model_exists = request.model_name_or_path in available_models

                    return {
                        "status": "success",
                        "model": request.model_name_or_path,
                        "message": f"Connected to {OPENAI_COMPATIBLE_URL}. Model '{request.model_name_or_path}' {'found' if model_exists else 'will be used (not verified)'}. Available: {', '.join(available_models[:3])}{'...' if len(available_models) > 3 else ''}",
                        "available_models": available_models,
                        "is_cloud": False
                    }
                else:
                    error_msg = f"Server returned status {response.status_code}: {response.text[:200]}"
                    logger.error(error_msg)
                    raise HTTPException(status_code=500, detail=f"Failed to connect: {error_msg}")

            except httpx.ConnectError as e:
                error_msg = f"Cannot reach server at {OPENAI_COMPATIBLE_URL}. Make sure Ollama/server is running. Error: {str(e)}"
                logger.error(error_msg)
                raise HTTPException(status_code=500, detail=error_msg)
            except httpx.RequestError as e:
                error_msg = f"Request failed to {OPENAI_COMPATIBLE_URL}: {str(e)}"
                logger.error(error_msg)
                raise HTTPException(status_code=500, detail=error_msg)

        else:
            raise HTTPException(status_code=400, detail=f"Unknown inference engine: {INFERENCE_ENGINE}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to load model: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to load model: {str(e)}")

@app.post("/unload_model")
async def unload_model(model_name: str):
    """Unload a model from memory."""
    global current_model

    if model_name not in loaded_models:
        raise HTTPException(status_code=404, detail=f"Model {model_name} not found")

    try:
        del loaded_models[model_name]
        if current_model == model_name:
            current_model = list(loaded_models.keys())[0] if loaded_models else None

        logger.info(f"Unloaded model: {model_name}")
        return {"status": "success", "model": model_name, "current_model": current_model}
    except Exception as e:
        logger.error(f"Failed to unload model: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to unload model: {str(e)}")

@app.post("/v1/completions")
async def create_completion(request: CompletionRequest):
    """Generate a completion from the model."""
    global current_model, openai_client

    if not current_model:
        raise HTTPException(status_code=400, detail="No model currently loaded")

    try:
        if INFERENCE_ENGINE == "vllm":
            if current_model not in loaded_models:
                raise HTTPException(status_code=400, detail="No model currently loaded")

            llm = loaded_models[current_model]

            # Create sampling parameters
            sampling_params = SamplingParams(
                temperature=request.temperature,
                top_p=request.top_p,
                max_tokens=request.max_tokens,
                stop=request.stop
            )

            # Generate completion
            logger.info(f"Generating completion with model: {current_model}")
            outputs = llm.generate([request.prompt], sampling_params)

            # Extract the generated text
            generated_text = outputs[0].outputs[0].text
            finish_reason = outputs[0].outputs[0].finish_reason

            return CompletionResponse(
                text=generated_text,
                model=current_model,
                finish_reason=finish_reason
            )

        elif INFERENCE_ENGINE == "openai_compatible":
            if not openai_client:
                openai_client = httpx.AsyncClient(base_url=OPENAI_COMPATIBLE_URL, timeout=60.0)

            # Call OpenAI-compatible API
            response = await openai_client.post(
                "/v1/completions",
                json={
                    "model": current_model,
                    "prompt": request.prompt,
                    "max_tokens": request.max_tokens,
                    "temperature": request.temperature,
                    "top_p": request.top_p,
                    "stop": request.stop,
                    "stream": False
                }
            )

            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=f"OpenAI-compatible server error: {response.text}")

            data = response.json()
            return CompletionResponse(
                text=data["choices"][0]["text"],
                model=current_model,
                finish_reason=data["choices"][0].get("finish_reason", "stop")
            )

        else:
            raise HTTPException(status_code=400, detail=f"Unknown inference engine: {INFERENCE_ENGINE}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Completion failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Completion failed: {str(e)}")


class AgentChatRequest(BaseModel):
    """Request for agent chat endpoint."""
    message: str
    conversation_history: Optional[List[Dict]] = None
    model: Optional[str] = None  # If not provided, uses current_model
    stream: bool = True
    project_context: Optional[Dict] = None  # Current project info (id, name, summary, status)


async def get_available_tools() -> List[ToolDefinition]:
    """
    Fetch available tools from MCP server.

    Returns:
        List of ToolDefinition objects
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8001/tools", timeout=5.0)
            response.raise_for_status()
            tools_data = response.json()

            return [
                ToolDefinition(
                    name=tool["name"],
                    description=tool["description"],
                    parameters=tool["parameters"]
                )
                for tool in tools_data
            ]
    except Exception as e:
        logger.warning(f"Failed to fetch tools from MCP server: {e}")
        return []


@app.post("/v1/agent/chat")
async def agent_chat(request: AgentChatRequest):
    """
    Agent chat endpoint with tool use and reasoning.
    Streams agent thinking steps, tool calls, and final answer.
    """
    global current_model

    # Determine which model to use
    model_name = request.model or current_model
    if not model_name:
        raise HTTPException(status_code=400, detail="No model specified or loaded")

    # Determine model prefix based on model name and inference engine
    # Cloud models (Anthropic, OpenAI, etc.) don't need prefixes
    is_cloud_model = any(model_name.startswith(prefix) for prefix in ['claude-', 'gpt-', 'anthropic/', 'openai/', 'gemini-'])

    if is_cloud_model:
        # Cloud provider model - use as-is
        agent_model = model_name
        logger.info(f"Using cloud model: {agent_model}")
    elif INFERENCE_ENGINE == "vllm" and model_name in loaded_models:
        # Local vLLM model
        agent_model = f"vllm/{model_name}"
        logger.info(f"Using vLLM model: {agent_model}")
    elif INFERENCE_ENGINE == "openai_compatible":
        # Local Ollama or other OpenAI-compatible server
        agent_model = f"ollama/{model_name}"
        logger.info(f"Using Ollama model: {agent_model}")
    else:
        # Fallback - use model name as-is
        agent_model = model_name
        logger.info(f"Using model: {agent_model}")

    try:
        # Fetch available tools from MCP server
        tools = await get_available_tools()
        logger.info(f"Loaded {len(tools)} tools from MCP server")

        # Convert conversation history to Message objects
        history = []
        if request.conversation_history:
            for msg in request.conversation_history:
                history.append(Message(
                    role=msg.get("role", "user"),
                    content=msg.get("content", "")
                ))

        # Create agent orchestrator
        agent = AgentOrchestrator(
            model=agent_model,
            tools=tools,
            config=AgentConfig(
                max_iterations=5,
                verbose=True
            ),
            project_context=request.project_context
        )

        # Stream agent steps
        async def generate_stream() -> AsyncGenerator[str, None]:
            """Generate SSE stream of agent steps."""
            try:
                async for step in agent.run(request.message, history):
                    # Convert step to JSON and send as SSE
                    data = step.to_stream_dict()
                    yield f"data: {json.dumps(data)}\n\n"

                # Send done signal
                yield f"data: {json.dumps({'type': 'done'})}\n\n"

            except Exception as e:
                logger.error(f"Agent execution failed: {str(e)}")
                error_data = {
                    "type": "error",
                    "error": str(e)
                }
                yield f"data: {json.dumps(error_data)}\n\n"

        if request.stream:
            # Return streaming response
            return StreamingResponse(
                generate_stream(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"
                }
            )
        else:
            # Collect all steps and return at once
            steps = []
            async for step in agent.run(request.message, history):
                steps.append(step.to_stream_dict())

            return {
                "steps": steps,
                "model": model_name
            }

    except Exception as e:
        logger.error(f"Agent chat failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Agent chat failed: {str(e)}")


@app.on_event("startup")
async def startup_event():
    """Auto-load model on startup if configured."""
    global startup_complete, current_model

    # Determine which model to load
    model_to_load = CURRENT_MODEL or DEFAULT_MODEL

    if INFERENCE_ENGINE == "openai_compatible":
        # For openai_compatible mode, always restore the saved model name
        if CURRENT_MODEL:
            current_model = CURRENT_MODEL
            logger.info(f"Restored model selection: {current_model}")
        logger.info(f"Using OpenAI-compatible server at {OPENAI_COMPATIBLE_URL}")
        logger.info("Models are managed by the external server")
    elif AUTO_LOAD_MODEL and INFERENCE_ENGINE == "vllm":
        logger.info(f"Auto-loading model: {model_to_load}")
        try:
            # Load model in background to not block server startup
            await load_default_model()
        except Exception as e:
            logger.error(f"Failed to auto-load model: {e}")
            logger.info("Server will continue without a loaded model")

    startup_complete = True
    logger.info(f"Server startup complete (engine: {INFERENCE_ENGINE}, model: {current_model or 'None'})")

async def load_default_model():
    """Load the default model (vLLM only)."""
    global current_model

    if INFERENCE_ENGINE != "vllm":
        logger.info("Skipping default model load (not using vLLM)")
        return

    try:
        logger.info(f"Loading default model: {DEFAULT_MODEL}")

        llm = LLM(
            model=DEFAULT_MODEL,
            gpu_memory_utilization=GPU_MEMORY_UTILIZATION,
            trust_remote_code=True,
            dtype="auto"
        )

        loaded_models[DEFAULT_MODEL] = llm
        current_model = DEFAULT_MODEL

        logger.info(f"Successfully loaded default model: {DEFAULT_MODEL}")
    except Exception as e:
        logger.error(f"Failed to load default model: {e}")
        raise

if __name__ == "__main__":
    logger.info(f"Starting Drakyn Inference Server")
    logger.info(f"Default model: {DEFAULT_MODEL}")
    logger.info(f"Auto-load enabled: {AUTO_LOAD_MODEL}")

    uvicorn.run(app, host="127.0.0.1", port=8000)
