# Development Guide

## Fast Development Workflow

### Option 1: Run Python Server Separately (Recommended)

This avoids restarting the Python server every time you make UI changes:

**Terminal 1 - Python Server (keep running):**
```bash
npm run server           # Linux/Mac/WSL
# Or on Windows CMD/PowerShell:
npm run server:win

# Or manually:
cd src/services/inference
source venv/bin/activate  # Windows: venv\Scripts\activate
python server.py
```

**Note:** The npm scripts automatically use the venv Python to avoid conflicts with system Python or conda environments.

**Terminal 2 - Electron App (restart as needed):**
```bash
npm run dev
# Or: npm start
```

**Benefits:**
- Python server stays running (no startup delay)
- Only restart Electron when you change UI
- Server keeps your loaded model in memory
- Much faster iteration cycle

### Option 2: Development Mode with Hot Reload

Run in development mode with DevTools:

```bash
npm run dev
```

**Features:**
- DevTools open automatically
- Press **Ctrl+R** (or **Cmd+R**) to reload UI without restarting
- No need to close and reopen the app for UI changes
- Python server keeps running in background

**Quick Reload:**
- Make UI changes (HTML/CSS/JS)
- Press **Ctrl+R** / **Cmd+R** to reload
- Changes appear instantly

### Option 3: Normal Mode

Production-like startup (no DevTools):

```bash
npm start
```

## Development Tips

### When to Restart What

**UI Changes (HTML/CSS/JS):**
- Option 1: Just press **Ctrl+R** in dev mode
- Option 2: Restart Electron app only (if server running separately)

**Python Changes (server.py, orchestrator.py, etc.):**
- Restart Python server
- Keep Electron app running (it will reconnect)

**Electron Changes (main.js, preload.js):**
- Must restart Electron app completely

### Port Configuration

- **Inference Server:** http://localhost:8000
- **MCP Server:** http://localhost:8001
- **Ollama:** http://localhost:11434 (or cnguyen-desktop.local:11434)

### Keyboard Shortcuts

**In Dev Mode (`npm run dev`):**
- **Ctrl+R** / **Cmd+R** - Reload UI
- **Ctrl+Shift+I** / **Cmd+Option+I** - Toggle DevTools
- **F12** - Toggle DevTools

## Scripts Reference

```bash
npm start           # Start app (production mode)
npm run dev         # Start app (development mode with DevTools)
npm run server      # Run Python server only (Linux/Mac/WSL)
npm run server:win  # Run Python server only (Windows)
npm run build       # Build distributable
npm run build:win   # Build for Windows
npm run build:mac   # Build for macOS
npm run build:linux # Build for Linux
```

## Troubleshooting

### Server won't start
- Check if port 8000 is already in use
- Verify Python venv is set up: `ls src/services/inference/venv`

### Can't connect to Ollama
- Make sure Ollama is running: `ollama list`
- Check URL in Settings tab

### UI changes not appearing
- Press **Ctrl+R** to reload
- If using separate server, just restart Electron app
