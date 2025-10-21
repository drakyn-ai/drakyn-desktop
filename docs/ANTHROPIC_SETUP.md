# Using Anthropic Claude Models

This guide explains how to configure and use Anthropic Claude models in Drakyn.

## Why Use Claude Models?

Claude models (especially Claude 3.5 Sonnet) are excellent for:
- **Tool/function calling** - Significantly better than local models
- **Following complex instructions** - Better reasoning capabilities
- **Understanding context** - Superior comprehension of multi-turn conversations
- **Reliability** - Consistent outputs without hallucinations

## Setup Instructions

### 1. Get an Anthropic API Key

1. Go to [Anthropic Console](https://console.anthropic.com/settings/keys)
2. Sign up or log in
3. Navigate to "API Keys" section
4. Click "Create Key"
5. Copy your API key (starts with `sk-ant-...`)

### 2. Configure in Drakyn

1. Open Drakyn application
2. Go to **Settings** page (sidebar)
3. Scroll to **Cloud API Keys** section
4. Paste your Anthropic API key in the field
5. (Optional) Add OpenAI API key if you want to use GPT models too
6. Click **Save API Keys**

The keys are saved to `src/services/inference/.env` file and never sent anywhere except to Anthropic/OpenAI.

### 3. Restart the Server

For the API keys to take effect, you need to restart the inference server:

**Option A: Restart from Settings**
1. Go to Settings page
2. Click "Stop Server"
3. Wait a few seconds
4. Click "Start Server"

**Option B: Restart the whole app**
- Close Drakyn completely
- Open it again

### 4. Select a Claude Model

1. Go to **Models** page
2. In the dropdown, select a Claude model from "Cloud Models" section:
   - **claude-3-5-sonnet-20241022** (Recommended - best for tool calling)
   - **claude-3-5-haiku-20241022** (Faster and cheaper)
   - **claude-3-opus-20240229** (Previous generation, very capable)
3. Click **Set Model**

### 5. Test It Out!

Go to the Chat page and try:
- "Can you read me my most recent email?" (Tests Gmail tool calling)
- "Find files with 'config' in them" (Tests file search)
- Any general question

Claude should respond intelligently and use tools when appropriate!

## Available Claude Models

| Model | Best For | Context Window | Speed |
|-------|----------|----------------|-------|
| **claude-3-5-sonnet-20241022** | Tool calling, complex tasks | 200K tokens | Medium |
| **claude-3-5-haiku-20241022** | Quick responses, simple tasks | 200K tokens | Fast |
| **claude-3-opus-20240229** | Maximum capability | 200K tokens | Slower |

## Pricing

Anthropic charges per token:
- Input tokens (what you send)
- Output tokens (what Claude generates)

Check [Anthropic's pricing page](https://anthropic.com/pricing) for current rates.

**Tip**: Start with Haiku for testing, then switch to Sonnet for production use.

## Comparison: Claude vs Local Models

| Feature | Claude 3.5 Sonnet | Local (gpt-oss:20b) |
|---------|-------------------|---------------------|
| Tool Calling | ✅ Excellent | ❌ Poor / None |
| Speed | ⚡ ~2-3s | ⚡ ~3-5s |
| Cost | 💰 API charges | 🆓 Free (local GPU) |
| Reliability | ✅ Very high | ⚠️ Inconsistent |
| Context Size | 📚 200K tokens | 📖 4K-8K tokens |
| Privacy | ☁️ Cloud (Anthropic) | 🔒 100% local |

## Troubleshooting

### "Model not working" or blank responses
1. Check your API key is correct
2. Ensure you restarted the server after adding the key
3. Check logs: `src/services/inference/logs/inference_server.log`
4. Look for "ANTHROPIC_API_KEY" in the logs

### "Invalid API key" error
- Your API key may be incorrect or expired
- Go to Settings and re-enter the key
- Make sure there are no extra spaces

### "Rate limit exceeded"
- You've hit Anthropic's usage limits
- Wait a few minutes and try again
- Check your usage at [Anthropic Console](https://console.anthropic.com)

### Model is expensive
- Switch to `claude-3-5-haiku-20241022` for lower costs
- Keep responses short to reduce output tokens
- Use local models for simple tasks, Claude for complex ones

## Next Steps

Once you have Claude working:
1. Set up Gmail integration (see [GMAIL_SETUP.md](GMAIL_SETUP.md))
2. Try asking Claude to help with emails
3. Experiment with file search and other tools
4. Adjust the system prompt in `src/services/inference/agent/prompts.py` if needed

## Support

If you encounter issues:
1. Check logs in `src/services/inference/logs/`
2. Verify your `.env` file has `ANTHROPIC_API_KEY=sk-ant-...`
3. Test with a simple question first
4. If all else fails, switch back to a local Ollama model temporarily
