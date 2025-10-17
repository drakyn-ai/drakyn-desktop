const { app, BrowserWindow } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let inferenceProcess;
let mcpProcess;

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

function startInferenceServer() {
  console.log('Starting inference server...');
  // TODO: Start Python inference server process
  // inferenceProcess = spawn('python', [path.join(__dirname, '../services/inference/server.py')]);
}

function startMCPServer() {
  console.log('Starting MCP server...');
  // TODO: Start Python MCP server process
  // mcpProcess = spawn('python', [path.join(__dirname, '../services/mcp/server.py')]);
}

function stopServices() {
  if (inferenceProcess) {
    inferenceProcess.kill();
  }
  if (mcpProcess) {
    mcpProcess.kill();
  }
}

app.on('ready', () => {
  createWindow();
  startInferenceServer();
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
