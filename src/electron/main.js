const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

let mainWindow;
let inferenceProcess;
let mcpProcess;
let setupInProgress = false;
let setupStatus = 'Starting...';

// Import setup utilities
let setupPythonEnvironment, venvExists;
try {
  const setupModule = require(path.join(__dirname, '../services/inference/setup.js'));
  setupPythonEnvironment = setupModule.setupPythonEnvironment;
  venvExists = setupModule.venvExists;
} catch (error) {
  console.error('Failed to load setup module:', error);
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
      preload: path.join(__dirname, 'preload.js')
    }
  });

  // Load the UI
  mainWindow.loadFile(path.join(__dirname, '../../public/index.html'));

  // Open DevTools in development mode
  if (process.argv.includes('--dev')) {
    mainWindow.webContents.openDevTools();
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function getPythonExecutable() {
  // Use venv Python if it exists
  const venvPython = process.platform === 'win32'
    ? path.join(__dirname, '../services/inference/venv/Scripts/python.exe')
    : path.join(__dirname, '../services/inference/venv/bin/python');

  if (fs.existsSync(venvPython)) {
    return venvPython;
  }

  return 'python'; // Fallback to system Python
}

async function ensurePythonEnvironment() {
  const serviceDir = path.join(__dirname, '../services/inference');
  const venvPath = path.join(serviceDir, 'venv');

  // Check if venv exists
  if (venvExists && venvExists(venvPath)) {
    console.log('Python environment already set up');
    updateSetupStatus('Python environment ready');
    return true;
  }

  // Setup needed
  console.log('Python environment not found, setting up...');
  setupInProgress = true;
  updateSetupStatus('Setting up Python environment for the first time...');

  try {
    if (!setupPythonEnvironment) {
      throw new Error('Setup module not available');
    }

    await setupPythonEnvironment(serviceDir, (message) => {
      console.log('[Setup]:', message);
      updateSetupStatus(message);
    });

    setupInProgress = false;
    updateSetupStatus('Setup complete!');
    return true;
  } catch (error) {
    console.error('Failed to setup Python environment:', error);
    setupInProgress = false;
    updateSetupStatus(`Setup failed: ${error.message}. Please install Python 3.10+ manually.`);
    return false;
  }
}

function updateSetupStatus(status) {
  setupStatus = status;
  if (mainWindow && mainWindow.webContents) {
    mainWindow.webContents.send('setup-status', status);
  }
}

async function startInferenceServer() {
  const serverPath = path.join(__dirname, '../services/inference/server.py');

  if (!fs.existsSync(serverPath)) {
    console.error('Inference server script not found:', serverPath);
    updateSetupStatus('Error: Server script not found');
    return;
  }

  // Ensure Python environment is set up
  updateSetupStatus('Checking Python environment...');
  const envReady = await ensurePythonEnvironment();
  if (!envReady) {
    console.error('Cannot start server: Python environment setup failed');
    return;
  }

  const pythonCmd = getPythonExecutable();
  console.log('Starting inference server with:', pythonCmd);
  updateSetupStatus('Starting inference server...');

  inferenceProcess = spawn(pythonCmd, [serverPath], {
    env: { ...process.env },
    cwd: path.join(__dirname, '../services/inference')
  });

  inferenceProcess.stdout.on('data', (data) => {
    console.log('[Inference Server]:', data.toString());
  });

  inferenceProcess.stderr.on('data', (data) => {
    console.error('[Inference Server Error]:', data.toString());
  });

  inferenceProcess.on('close', (code) => {
    console.log(`Inference server exited with code ${code}`);
    updateSetupStatus('Server stopped');
  });

  inferenceProcess.on('error', (error) => {
    console.error('Failed to start inference server:', error);
    updateSetupStatus(`Server error: ${error.message}`);
  });

  updateSetupStatus('Server running, loading model...');
}

function startMCPServer() {
  const serverPath = path.join(__dirname, '../services/mcp/server.py');

  if (!fs.existsSync(serverPath)) {
    console.log('MCP server script not found, skipping...');
    return;
  }

  const pythonCmd = getPythonExecutable();
  console.log('Starting MCP server with:', pythonCmd);

  mcpProcess = spawn(pythonCmd, [serverPath], {
    env: { ...process.env },
    cwd: path.join(__dirname, '../services/mcp')
  });

  mcpProcess.stdout.on('data', (data) => {
    console.log('[MCP Server]:', data.toString());
  });

  mcpProcess.stderr.on('data', (data) => {
    console.error('[MCP Server Error]:', data.toString());
  });

  mcpProcess.on('close', (code) => {
    console.log(`MCP server exited with code ${code}`);
  });
}

function stopServices() {
  if (inferenceProcess) {
    console.log('Stopping inference server...');
    inferenceProcess.kill('SIGTERM');
    inferenceProcess = null;
  }
  if (mcpProcess) {
    console.log('Stopping MCP server...');
    mcpProcess.kill('SIGTERM');
    mcpProcess = null;
  }
}

// IPC handlers for server status
ipcMain.handle('get-server-status', async () => {
  return {
    inference: inferenceProcess !== null && !inferenceProcess.killed,
    mcp: mcpProcess !== null && !mcpProcess.killed,
    setupInProgress,
    setupStatus
  };
});

ipcMain.handle('get-setup-status', async () => {
  return {
    setupInProgress,
    status: setupStatus
  };
});

app.on('ready', () => {
  createWindow();
  startInferenceServer();
  // Start MCP server for agent tools
  startMCPServer();
});

app.on('window-all-closed', () => {
  stopServices();
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});

app.on('before-quit', () => {
  stopServices();
});
