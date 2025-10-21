# Drakyn CLI

A command-line interface for interacting with the Drakyn AI Agent. The CLI provides the same functionality as the Electron UI but from the terminal, making it perfect for:
- Development and testing in WSL/Linux
- Automation and scripting
- Remote server management
- Quick interactions without launching the GUI

## Installation

The CLI is included with drakyn-desktop. Install Python dependencies:

```bash
pip3 install -r src/cli/requirements.txt
```

Dependencies:
- `click` >= 8.0.0 - CLI framework
- `requests` >= 2.31.0 - HTTP client

## Usage

### Running the CLI

**Direct execution:**
```bash
./drakyn [command] [options]
```

**Via npm:**
```bash
npm run cli -- [command] [options]
```

**Direct Python:**
```bash
python3 src/cli/cli.py [command] [options]
```

### Available Commands

#### `status` - Check Server Status

Check if the backend server is running and view current configuration.

```bash
./drakyn status
```

Output:
```
✓ Server is running
  Engine: vllm
  Current Model: qwen2.5-coder:3b
```

**npm shortcut:**
```bash
npm run cli:status
```

#### `models` - List Models

View currently loaded models.

```bash
./drakyn models
```

Output:
```
Loaded Models:
  • qwen2.5-coder:3b (active)
  • llama3.2:3b
```

**npm shortcut:**
```bash
npm run cli:models
```

#### `load` - Load a Model

Load a model for inference.

```bash
./drakyn load <model_name> [options]
```

**Options:**
- `--gpu-memory` - GPU memory utilization, 0.1-1.0 (default: 0.9)
- `--tensor-parallel` - Tensor parallel size (default: 1)

**Examples:**
```bash
# Load a local Ollama model
./drakyn load qwen2.5-coder:3b

# Load a cloud model (requires API key in settings)
./drakyn load claude-sonnet-4-5

# Load with custom GPU memory
./drakyn load qwen2.5:7b --gpu-memory 0.8
```

#### `chat` - Interactive Chat

Start an interactive chat session with the agent.

```bash
./drakyn chat [options]
```

**Options:**
- `--stream/--no-stream` - Enable/disable streaming responses (default: enabled)

**Example:**
```bash
./drakyn chat
```

Interactive session:
```
Drakyn Agent Chat
Type your message and press Enter. Type 'exit' or 'quit' to end.

You: What is the weather like?
[Using tool: get_weather]
Agent: Based on the weather data, it's currently sunny and 72°F.

You: exit
Goodbye!
```

**npm shortcut:**
```bash
npm run cli:chat
```

**Features:**
- Real-time streaming responses
- Tool usage indicators
- Thinking status updates
- Clean, colored output
- Exit with 'exit', 'quit', or Ctrl+C

## Workflow Examples

### Development Workflow

**1. Start the backend server:**
```bash
# In one terminal
npm run server      # Linux/Mac
npm run server:win  # Windows
```

**2. Check status:**
```bash
# In another terminal
./drakyn status
```

**3. Load a model:**
```bash
./drakyn load qwen2.5-coder:3b
```

**4. Start chatting:**
```bash
./drakyn chat
```

### Quick Status Check

```bash
# One-liner to check if everything is ready
./drakyn status && echo "Ready to chat!" || echo "Server not running"
```

### Testing Agent Responses

```bash
# Start chat session for testing
npm run cli:chat
```

## CLI vs Electron UI

The CLI mirrors the Electron UI functionality:

| Feature | Electron UI | CLI |
|---------|-------------|-----|
| Check Status | Status indicator | `./drakyn status` |
| List Models | Models page | `./drakyn models` |
| Load Model | Models page → Set Model | `./drakyn load <name>` |
| Chat with Agent | Chat page | `./drakyn chat` |
| Settings | Settings page | Environment variables/config files |

## Configuration

The CLI uses the same configuration as the Electron app:

**API Base URL:**
```bash
export DRAKYN_API_URL=http://localhost:8000
./drakyn status
```

**Server Configuration:**
Edit `src/services/inference/.env`:
```bash
INFERENCE_ENGINE=vllm  # or openai_compatible
OPENAI_COMPATIBLE_URL=http://localhost:11434  # for Ollama
```

## Troubleshooting

### Server Not Running

```
✗ Server is not running
  Expected at: http://127.0.0.1:8000
  Start it with: npm run server
```

**Solution:** Start the backend server:
```bash
npm run server      # Linux/Mac
npm run server:win  # Windows
```

### Connection Refused

If the CLI can't connect:
1. Check if server is running: `ps aux | grep python.*server.py`
2. Check if port 8000 is in use: `netstat -an | grep 8000`
3. Try restarting the server

### Model Not Loaded

```
No model loaded
```

**Solution:** Load a model first:
```bash
./drakyn load qwen2.5-coder:3b
```

## Advanced Usage

### Scripting

The CLI is designed for scripting. Exit codes indicate success/failure:

```bash
#!/bin/bash

# Check if server is running
if ./drakyn status > /dev/null 2>&1; then
    echo "Server is ready"
    ./drakyn load qwen2.5-coder:3b
else
    echo "Starting server..."
    npm run server &
    sleep 5
    ./drakyn status
fi
```

### Automation

```bash
# Auto-load model on server start
npm run server &
sleep 5
./drakyn load qwen2.5-coder:3b
./drakyn status
```

### Testing

Use the CLI to test agent functionality:

```bash
# Test model loading
./drakyn load qwen2.5-coder:3b
[ $? -eq 0 ] && echo "✓ Model loaded" || echo "✗ Failed"

# Test chat endpoint
./drakyn chat --no-stream <<< "Hello, test message"
```

## Environment Variables

- `DRAKYN_API_URL` - Override default API base URL (default: http://127.0.0.1:8000)

Example:
```bash
export DRAKYN_API_URL=http://192.168.1.100:8000
./drakyn status
```

## Future Enhancements

Planned features:
- [ ] Non-interactive chat mode for scripting
- [ ] Config management commands
- [ ] Server start/stop from CLI
- [ ] Model search and browse
- [ ] Conversation history
- [ ] Output format options (JSON, plain text)

## Help

Get help for any command:

```bash
./drakyn --help
./drakyn chat --help
./drakyn load --help
```

## Comparison with Electron UI

**Use the CLI when:**
- Developing in WSL/Linux
- Automating tasks
- Quick interactions
- Remote server management
- Prefer terminal workflows

**Use the Electron UI when:**
- On Windows/Mac desktop
- Need visual interface
- Managing multiple conversations
- Configuring complex settings
- Prefer graphical workflows

Both interfaces use the same backend, so you can switch between them freely.
