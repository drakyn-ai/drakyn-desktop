"""
Inference server for running LLM models locally.
Supports vLLM, SGLang, and other backends via abstraction layer.
"""
import asyncio
import logging
import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import uvicorn
from vllm import LLM, SamplingParams
from vllm.outputs import RequestOutput

# Load environment variables
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
    logger = logging.getLogger(__name__)
    logger.info(f"Loaded config from {env_path}")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "Qwen/Qwen2.5-0.5B-Instruct")
AUTO_LOAD_MODEL = os.getenv("AUTO_LOAD_MODEL", "true").lower() == "true"
GPU_MEMORY_UTILIZATION = float(os.getenv("GPU_MEMORY_UTILIZATION", "0.9"))

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
loaded_models: Dict[str, LLM] = {}
current_model: Optional[str] = None
startup_complete: bool = False

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

@app.post("/load_model")
async def load_model(request: LoadModelRequest):
    """Load a model into memory using vLLM."""
    global current_model

    try:
        logger.info(f"Loading model: {request.model_name_or_path}")

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

        logger.info(f"Successfully loaded model: {current_model}")
        return {
            "status": "success",
            "model": request.model_name_or_path,
            "message": "Model loaded successfully"
        }

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
    global current_model

    if not current_model or current_model not in loaded_models:
        raise HTTPException(status_code=400, detail="No model currently loaded")

    try:
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

    except Exception as e:
        logger.error(f"Completion failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Completion failed: {str(e)}")

@app.on_event("startup")
async def startup_event():
    """Auto-load default model on startup if configured."""
    global startup_complete

    if AUTO_LOAD_MODEL:
        logger.info(f"Auto-loading default model: {DEFAULT_MODEL}")
        try:
            # Load model in background to not block server startup
            await load_default_model()
        except Exception as e:
            logger.error(f"Failed to auto-load model: {e}")
            logger.info("Server will continue without a loaded model")

    startup_complete = True
    logger.info("Server startup complete")

async def load_default_model():
    """Load the default model."""
    global current_model

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
