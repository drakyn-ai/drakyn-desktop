/**
 * Simple HTTP server for IPC communication between Python services and Electron.
 *
 * Allows Python background monitor to send notifications to Electron main process.
 */
const http = require('http');
const { Notification } = require('electron');

let mainWindow = null;
let suggestionQueue = [];

/**
 * Create and start the IPC server.
 *
 * @param {BrowserWindow} window - The main Electron window
 * @param {number} port - Port to listen on (default: 9999)
 */
function createIPCServer(window, port = 9999) {
  mainWindow = window;

  const server = http.createServer(async (req, res) => {
    // Enable CORS
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    // Handle preflight
    if (req.method === 'OPTIONS') {
      res.writeHead(200);
      res.end();
      return;
    }

    // Only accept POST requests
    if (req.method !== 'POST') {
      res.writeHead(405, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'Method not allowed' }));
      return;
    }

    // Parse request body
    let body = '';
    req.on('data', chunk => {
      body += chunk.toString();
    });

    req.on('end', () => {
      try {
        const data = JSON.parse(body);

        // Route based on endpoint
        if (req.url === '/notify') {
          handleNotification(data);
          res.writeHead(200, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ success: true }));
        } else if (req.url === '/suggestion') {
          handleSuggestion(data);
          res.writeHead(200, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ success: true }));
        } else {
          res.writeHead(404, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ error: 'Endpoint not found' }));
        }
      } catch (error) {
        console.error('[IPC Server] Error:', error);
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: error.message }));
      }
    });
  });

  server.listen(port, '127.0.0.1', () => {
    console.log(`[IPC Server] Listening on http://127.0.0.1:${port}`);
  });

  return server;
}

/**
 * Handle notification request from Python service.
 */
function handleNotification(data) {
  const { title, body } = data;

  console.log('[IPC Server] Notification:', title, '-', body);

  // Show system notification
  const notification = new Notification({
    title: title || 'Drakyn',
    body: body || 'No message',
    silent: false
  });

  notification.on('click', () => {
    // Focus window when notification clicked
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }
  });

  notification.show();

  // Also send to renderer process for in-app display
  if (mainWindow && mainWindow.webContents) {
    mainWindow.webContents.send('proactive-suggestion', data);
  }
}

/**
 * Handle suggestion from background monitor.
 */
function handleSuggestion(suggestion) {
  console.log('[IPC Server] Suggestion:', suggestion);

  // Add to queue
  suggestionQueue.push({
    ...suggestion,
    timestamp: new Date().toISOString(),
    status: 'pending'
  });

  // Notify renderer
  if (mainWindow && mainWindow.webContents) {
    mainWindow.webContents.send('new-suggestion', suggestion);
  }
}

/**
 * Get pending suggestions.
 */
function getPendingSuggestions() {
  return suggestionQueue.filter(s => s.status === 'pending');
}

/**
 * Mark suggestion as handled.
 */
function markSuggestionHandled(suggestionId, action) {
  const suggestion = suggestionQueue.find(s => s.id === suggestionId);
  if (suggestion) {
    suggestion.status = action; // 'accepted', 'dismissed', 'ignored'
    suggestion.handledAt = new Date().toISOString();
  }
}

module.exports = {
  createIPCServer,
  getPendingSuggestions,
  markSuggestionHandled
};
