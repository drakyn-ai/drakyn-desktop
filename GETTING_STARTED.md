# Getting Started with Drakyn Desktop

Welcome! Drakyn Desktop makes it easy to run AI models locally on your machine.

## First Time Setup

### What You Need

Just have **Python 3.10+** installed on your system. That's it!

Check if you have Python:
```bash
python --version
```

If not, download from: https://www.python.org/downloads/

### Running the App

```bash
npm run dev
```

On **first run**, the app will automatically:

1. Create a Python virtual environment (30 seconds)
2. Install AI dependencies like vLLM (3-5 minutes)
3. Download the default model (2-3 minutes)
4. Start the chat interface

**Total first-run time: ~5-10 minutes**

Watch the connection status indicator in the Chat tab - it will turn green when ready!

## Using the App

### Chat Tab
- Wait for green "Ready" status
- Type messages to talk with the AI
- Model responds based on your input

### Models Tab
- See currently loaded model
- Load different models from HuggingFace
- Adjust GPU memory settings
- Unload models to free memory

### Quick Tips

**Change the default model:**
Edit `src/services/inference/.env` and change `DEFAULT_MODEL`

**Recommended starter models:**
- `Qwen/Qwen2.5-0.5B-Instruct` (500MB, fast, default)
- `Qwen/Qwen2.5-1.5B-Instruct` (1.5GB, better quality)
- `Qwen/Qwen2.5-3B-Instruct` (3GB, best quality for most GPUs)

**GPU Memory:**
- 8GB GPU: Use 0.5B or 1.5B models
- 12GB GPU: Use up to 7B models
- 16GB+ GPU: Use 7B-14B models

## Need Help?

**Setup taking too long?**
- First run downloads ~2-3GB of dependencies
- Check your internet connection
- Look at the console logs for progress

**Chat not responding?**
- Make sure status indicator is green
- Check Models tab to confirm model is loaded
- Try refreshing the page

**Python errors?**
- Verify Python 3.10+ is installed
- Make sure CUDA toolkit is installed (for GPU support)
- Check Electron console (DevTools) for detailed errors

## What's Next?

The app will remember your setup! Next time you run it:
- Starts in ~10 seconds
- No downloads needed
- Model loads automatically
- Ready to chat immediately

Enjoy chatting with your local AI! 🚀
