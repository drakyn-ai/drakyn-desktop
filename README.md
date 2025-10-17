# Drakyn Desktop

Native desktop application for running LLM agents locally on macOS and Windows.

## Architecture

Drakyn Desktop is built with a modular architecture consisting of three main components:

### 1. Inference Server (Python + vLLM)
- Located in `src/services/inference/`
- Handles LLM model loading and inference
- Provides REST API for completions
- Supports multiple models running concurrently
- Port: 8000

### 2. MCP Server (Python)
- Located in `src/services/mcp/`
- Implements Model Context Protocol for tool integration
- Manages agent capabilities and tool execution
- Extensible tool registry
- Port: 8001

### 3. Desktop UI (Electron + JavaScript)
- Located in `src/electron/` and `public/`
- Cross-platform native application
- Manages Python backend services
- Provides chat interface and agent management
- Configuration UI for models and settings

## Project Structure

```
drakyn-desktop/
├── src/
│   ├── electron/          # Electron main process
│   │   ├── main.js       # App entry point
│   │   └── preload.js    # Preload script
│   └── services/
│       ├── inference/    # vLLM inference server
│       │   ├── server.py
│       │   └── requirements.txt
│       └── mcp/          # MCP server
│           ├── server.py
│           └── requirements.txt
├── public/               # UI assets
│   ├── index.html
│   ├── styles.css
│   └── app.js
└── package.json
```

## Development Setup

### Prerequisites
- Node.js 18+
- Python 3.10+
- CUDA (optional, for GPU acceleration)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/drakyn-ai/drakyn-desktop.git
cd drakyn-desktop
```

2. Install Node.js dependencies:
```bash
npm install
```

3. Set up Python environments:
```bash
# Inference server
cd src/services/inference
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# MCP server
cd ../mcp
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Running in Development

Start the application in development mode:
```bash
npm run dev
```

This will:
- Launch the Electron app with DevTools open
- Start the inference server on port 8000
- Start the MCP server on port 8001

## Building

### Automated Builds (Recommended)

Builds for all platforms (macOS, Windows, Linux) are automated using GitHub Actions:

1. **Automatic on Tag Push**: Create a new tag to trigger a release build
   ```bash
   git tag v0.2.0
   git push origin v0.2.0
   ```
   This will build for all platforms and create a GitHub release automatically.

2. **Manual Trigger**: Go to GitHub Actions → "Manual Build" → "Run workflow"
   - Choose which platform(s) to build
   - Download artifacts when complete

### Local Builds

Build for your current platform:
```bash
npm run build
```

Or build for specific platforms:
```bash
npm run build:mac    # macOS (DMG, ZIP) - requires macOS
npm run build:win    # Windows (NSIS installer, portable) - requires Windows
npm run build:linux  # Linux (AppImage, DEB) - requires Linux
```

**Note**: macOS and Windows builds require their respective operating systems unless using GitHub Actions.

## Features (Roadmap)

- [ ] Model management (download, load, unload)
- [ ] Multiple agent configurations
- [ ] Chat interface with streaming responses
- [ ] Tool integration via MCP
- [ ] GPU/CPU selection
- [ ] Conversation history
- [ ] System resource monitoring
- [ ] Import/export agent configs
- [ ] Plugin system for custom tools

## Technology Stack

- **Frontend**: Electron, HTML/CSS/JavaScript
- **Backend Services**: Python, FastAPI, Uvicorn
- **Inference Engine**: vLLM (or SGLang)
- **Protocol**: Model Context Protocol (MCP)

## License

MIT

## Contributing

Contributions welcome! Please open an issue or PR.
