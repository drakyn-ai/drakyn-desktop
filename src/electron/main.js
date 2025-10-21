const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');
const { createIPCServer } = require('./ipc_server');

let mainWindow;
let inferenceProcess;
let mcpProcess;
let monitorProcess;
let ipcServer;
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
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    }
  });

  // Load the UI
  mainWindow.loadFile(path.join(__dirname, '../../public/index.html'));

  // Enable development mode with --dev flag
  if (process.argv.includes('--dev')) {
    mainWindow.webContents.openDevTools();

    // Enable quick reload with Ctrl+R / Cmd+R
    mainWindow.webContents.on('before-input-event', (event, input) => {
      if ((input.control || input.meta) && input.key.toLowerCase() === 'r') {
        mainWindow.reload();
      }
    });
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

function startMonitorService() {
  const servicePath = path.join(__dirname, '../services/monitor/service.py');

  if (!fs.existsSync(servicePath)) {
    console.log('Monitor service script not found, skipping...');
    return;
  }

  const pythonCmd = getPythonExecutable();
  console.log('Starting background monitor service with:', pythonCmd);

  monitorProcess = spawn(pythonCmd, [servicePath], {
    env: {
      ...process.env,
      CHECK_INTERVAL_MINUTES: '30'  // Check every 30 minutes
    },
    cwd: path.join(__dirname, '../services/monitor')
  });

  monitorProcess.stdout.on('data', (data) => {
    console.log('[Monitor Service]:', data.toString());
  });

  monitorProcess.stderr.on('data', (data) => {
    console.error('[Monitor Service Error]:', data.toString());
  });

  monitorProcess.on('close', (code) => {
    console.log(`Monitor service exited with code ${code}`);
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
  if (monitorProcess) {
    console.log('Stopping monitor service...');
    monitorProcess.kill('SIGTERM');
    monitorProcess = null;
  }
}

// Register IPC handlers - called after app is ready
function setupIPCHandlers() {
  // IPC handlers for server status
  ipcMain.handle('get-server-status', async () => {
    return {
      inference: inferenceProcess && inferenceProcess.killed === false,
      mcp: mcpProcess && mcpProcess.killed === false,
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

  // IPC handler to update .env configuration
  ipcMain.handle('update-config', async (event, config) => {
    try {
      const envPath = path.join(__dirname, '../services/inference/.env');

      if (!fs.existsSync(envPath)) {
        throw new Error('.env file not found');
      }

      // Read current .env file
      let envContent = fs.readFileSync(envPath, 'utf8');
      const lines = envContent.split('\n');

      // Update the relevant lines
      let engineUpdated = false;
      let urlUpdated = false;
      const newLines = [];

      for (const line of lines) {
        if (line.startsWith('INFERENCE_ENGINE=')) {
          newLines.push(`INFERENCE_ENGINE=${config.inference_engine}`);
          engineUpdated = true;
        } else if (line.startsWith('OPENAI_COMPATIBLE_URL=')) {
          newLines.push(`OPENAI_COMPATIBLE_URL=${config.openai_compatible_url}`);
          urlUpdated = true;
        } else {
          newLines.push(line);
        }
      }

      // Add lines if they didn't exist
      if (!engineUpdated) {
        newLines.unshift(`INFERENCE_ENGINE=${config.inference_engine}`);
      }
      if (!urlUpdated) {
        newLines.splice(1, 0, `OPENAI_COMPATIBLE_URL=${config.openai_compatible_url}`);
      }

      // Write back to file
      fs.writeFileSync(envPath, newLines.join('\n'));

      console.log('Configuration updated:', config);
      return { success: true, message: 'Configuration updated successfully' };
    } catch (error) {
      console.error('Failed to update config:', error);
      return { success: false, error: error.message };
    }
  });

  // IPC handler to read current config
  ipcMain.handle('get-config', async () => {
    try {
      const envPath = path.join(__dirname, '../services/inference/.env');

      if (!fs.existsSync(envPath)) {
        return {
          inference_engine: 'vllm',
          openai_compatible_url: 'http://localhost:11434'
        };
      }

      const envContent = fs.readFileSync(envPath, 'utf8');
      const lines = envContent.split('\n');

      const config = {
        inference_engine: 'vllm',
        openai_compatible_url: 'http://localhost:11434'
      };

      for (const line of lines) {
        if (line.startsWith('INFERENCE_ENGINE=')) {
          config.inference_engine = line.split('=')[1].trim();
        } else if (line.startsWith('OPENAI_COMPATIBLE_URL=')) {
          config.openai_compatible_url = line.split('=')[1].trim();
        }
      }

      return config;
    } catch (error) {
      console.error('Failed to read config:', error);
      return {
        inference_engine: 'vllm',
        openai_compatible_url: 'http://localhost:11434'
      };
    }
  });

  // IPC handlers for manual server control
  ipcMain.handle('start-inference-server', async () => {
    if (inferenceProcess && inferenceProcess.killed === false) {
      return { success: false, message: 'Server already running' };
    }

    try {
      await startInferenceServer();
      return { success: true, message: 'Server started' };
    } catch (error) {
      return { success: false, error: error.message };
    }
  });

  ipcMain.handle('stop-inference-server', async () => {
    if (!inferenceProcess || (inferenceProcess.killed !== false)) {
      return { success: false, message: 'Server not running' };
    }

    try {
      inferenceProcess.kill('SIGTERM');
      inferenceProcess = null;
      updateSetupStatus('Server stopped');
      return { success: true, message: 'Server stopped' };
    } catch (error) {
      return { success: false, error: error.message };
    }
  });
}

app.on('ready', () => {
  setupIPCHandlers();
  createWindow();

  // Start IPC server for Python services to communicate with Electron
  ipcServer = createIPCServer(mainWindow, 9999);

  // Auto-start inference server (starts fast in openai_compatible mode)
  startInferenceServer();
  // Start MCP server for agent tools
  startMCPServer();
  // Start background monitor service for proactive suggestions
  startMonitorService();
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

  // Close IPC server
  if (ipcServer) {
    ipcServer.close();
    ipcServer = null;
  }
});
