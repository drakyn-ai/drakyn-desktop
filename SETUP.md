# Drakyn Desktop Setup Guide

## Prerequisites

**Required:**
- Python 3.10 or later installed and available in PATH
- CUDA-capable GPU with CUDA toolkit installed (for vLLM)
- At least 8GB GPU memory for small models

**The app will automatically:**
- Create a Python virtual environment
- Install all dependencies (vLLM, FastAPI, etc.)
- Download and load the default model (Qwen2.5-0.5B)

## Quick Start

### 1. Just Run It!

```bash
npm run dev
```

That's it! The app will:
1. Check for Python environment
2. Auto-create venv and install dependencies (first run only)
3. Start the inference server
4. Auto-load the default model
5. Enable chat when ready

**First run takes 5-10 minutes** to download dependencies and the model.

### 2. Configure Default Model (Optional)

Edit `src/services/inference/.env`:

```bash
# Change the default model
DEFAULT_MODEL=Qwen/Qwen2.5-0.5B-Instruct

# Enable/disable auto-loading
AUTO_LOAD_MODEL=true

# Adjust GPU memory usage (0.0 to 1.0)
GPU_MEMORY_UTILIZATION=0.9
```

### 3. Using the App

- **Chat Tab**: Talk to the AI model once the connection status shows "Ready"
- **Models Tab**: Load/unload different models, view current model
- **Connection Status**: Green dot = ready, Yellow = loading, Red = disconnected

## Supported Models

The app works with any vLLM-compatible model from HuggingFace:

### Small Models (< 2GB VRAM)
- `Qwen/Qwen2.5-0.5B-Instruct` (default)
- `Qwen/Qwen2.5-1.5B-Instruct`
- `microsoft/phi-2`

### Medium Models (4-8GB VRAM)
- `Qwen/Qwen2.5-3B-Instruct`
- `Qwen/Qwen2.5-7B-Instruct`
- `meta-llama/Llama-3.2-3B-Instruct`

### Large Models (16GB+ VRAM)
- `Qwen/Qwen2.5-14B-Instruct`
- `meta-llama/Llama-3.1-8B-Instruct`

## Switching to SGLang (Future)

The server is designed to support multiple backends. To use SGLang instead of vLLM:

1. Update `requirements.txt` to use `sglang` instead of `vllm`
2. Modify the server backend implementation
3. Keep the same API interface

The frontend will work without changes.

## What Happens on First Run?

1. **Checking Python** - App finds Python installation
2. **Creating venv** - Sets up isolated Python environment
3. **Installing dependencies** - Downloads vLLM, PyTorch, FastAPI (3-5 minutes)
4. **Starting server** - Launches inference server
5. **Loading model** - Downloads and loads Qwen2.5-0.5B from HuggingFace (2-3 minutes)
6. **Ready!** - Green status indicator, chat enabled

Subsequent runs skip steps 1-3 and start immediately.

## Troubleshooting

### Python Not Found
- Install Python 3.10+ from python.org
- Ensure Python is in your system PATH
- Restart terminal and try again

### CUDA/GPU Issues
- Ensure CUDA toolkit is installed
- Check GPU memory: `nvidia-smi`
- Lower `GPU_MEMORY_UTILIZATION` in `.env`

### Model Loading Fails
- Check internet connection (for HuggingFace downloads)
- Verify model name is correct
- Check available GPU memory
- Try a smaller model first

### Server Won't Start
- Check Python installation: `python --version`
- Verify all dependencies installed: `pip list`
- Check server logs in Electron DevTools console

### Chat Not Responding
- Wait for model to fully load (check connection status)
- Verify server is running (Models tab > Server Status)
- Check browser console for errors (F12)

## Development

### Running Server Standalone
```bash
cd src/services/inference
python server.py
```

Access at: http://127.0.0.1:8000/docs

### Disable Auto-Load for Testing
Set in `.env`:
```
AUTO_LOAD_MODEL=false
```

Then manually load models via the Models tab or API.
