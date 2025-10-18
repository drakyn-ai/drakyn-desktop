const API_BASE_URL = 'http://127.0.0.1:8000';

// Simple page navigation
document.querySelectorAll('.sidebar a').forEach(link => {
  link.addEventListener('click', (e) => {
    e.preventDefault();
    const page = e.target.dataset.page;

    // Hide all pages
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));

    // Show selected page
    document.getElementById(`${page}-page`).classList.add('active');

    // Refresh models list when switching to models page
    if (page === 'models') {
      refreshModelsList();
      checkServerStatus();
    }
  });
});

// Chat functionality
const messageInput = document.getElementById('message-input');
const sendButton = document.getElementById('send-button');
const chatMessages = document.getElementById('chat-messages');

function addMessage(text, isUser = true) {
  const messageDiv = document.createElement('div');
  messageDiv.style.padding = '0.5rem';
  messageDiv.style.marginBottom = '0.5rem';
  messageDiv.style.backgroundColor = isUser ? '#2a2d2e' : '#1e1e1e';
  messageDiv.style.borderRadius = '4px';
  messageDiv.style.borderLeft = isUser ? '3px solid #007acc' : '3px solid #858585';
  messageDiv.textContent = `${isUser ? 'You' : 'Agent'}: ${text}`;
  chatMessages.appendChild(messageDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

async function sendMessage() {
  const message = messageInput.value.trim();
  if (!message) return;

  addMessage(message, true);
  messageInput.value = '';

  try {
    const response = await fetch(`${API_BASE_URL}/v1/completions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        prompt: message,
        max_tokens: 512,
        temperature: 0.7
      })
    });

    if (response.ok) {
      const data = await response.json();
      addMessage(data.text, false);
    } else {
      const error = await response.text();
      addMessage(`Error: ${error}`, false);
    }
  } catch (error) {
    addMessage(`Connection error: ${error.message}. Make sure a model is loaded.`, false);
  }
}

sendButton.addEventListener('click', sendMessage);
messageInput.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') {
    sendMessage();
  }
});

// Model management functionality
async function checkServerStatus() {
  const statusEl = document.getElementById('inference-status');
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    if (response.ok) {
      const data = await response.json();
      statusEl.textContent = `Running (Current model: ${data.current_model || 'None'})`;
      statusEl.style.color = '#4ec9b0';
    } else {
      statusEl.textContent = 'Not responding';
      statusEl.style.color = '#f48771';
    }
  } catch (error) {
    statusEl.textContent = 'Offline';
    statusEl.style.color = '#f48771';
  }
}

async function refreshModelsList() {
  const listEl = document.getElementById('loaded-models-list');
  try {
    const response = await fetch(`${API_BASE_URL}/models`);
    if (response.ok) {
      const data = await response.json();
      if (data.models.length === 0) {
        listEl.innerHTML = '<p>No models loaded</p>';
      } else {
        listEl.innerHTML = data.models.map(model => `
          <div class="model-item">
            <span>${model.name}</span>
            ${model.active ? '<span class="badge">Active</span>' : ''}
            <button onclick="unloadModel('${model.name}')" class="btn-danger-small">Unload</button>
          </div>
        `).join('');
      }
    } else {
      listEl.innerHTML = '<p>Error loading models list</p>';
    }
  } catch (error) {
    listEl.innerHTML = '<p>Cannot connect to server</p>';
  }
}

async function loadModel() {
  const modelPath = document.getElementById('model-path').value.trim();
  const gpuMemory = parseFloat(document.getElementById('gpu-memory').value);
  const tensorParallel = parseInt(document.getElementById('tensor-parallel').value);
  const statusEl = document.getElementById('load-status');
  const loadBtn = document.getElementById('load-model-btn');

  if (!modelPath) {
    statusEl.textContent = 'Please enter a model name or path';
    statusEl.style.color = '#f48771';
    return;
  }

  loadBtn.disabled = true;
  statusEl.textContent = 'Loading model... This may take several minutes.';
  statusEl.style.color = '#dcdcaa';

  try {
    const response = await fetch(`${API_BASE_URL}/load_model`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model_name_or_path: modelPath,
        gpu_memory_utilization: gpuMemory,
        tensor_parallel_size: tensorParallel
      })
    });

    const data = await response.json();

    if (response.ok) {
      statusEl.textContent = `Success: ${data.message}`;
      statusEl.style.color = '#4ec9b0';
      refreshModelsList();
      checkServerStatus();
    } else {
      statusEl.textContent = `Error: ${data.detail}`;
      statusEl.style.color = '#f48771';
    }
  } catch (error) {
    statusEl.textContent = `Connection error: ${error.message}`;
    statusEl.style.color = '#f48771';
  } finally {
    loadBtn.disabled = false;
  }
}

async function unloadModel(modelName) {
  try {
    const response = await fetch(`${API_BASE_URL}/unload_model?model_name=${encodeURIComponent(modelName)}`, {
      method: 'POST'
    });

    if (response.ok) {
      refreshModelsList();
      checkServerStatus();
    } else {
      alert('Failed to unload model');
    }
  } catch (error) {
    alert(`Error: ${error.message}`);
  }
}

// Connection status monitoring for chat
let connectionCheckInterval = null;
let isConnected = false;

async function checkChatConnection() {
  const indicator = document.getElementById('connection-indicator');
  const text = document.getElementById('connection-text');
  const messageInput = document.getElementById('message-input');
  const sendButton = document.getElementById('send-button');

  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    if (response.ok) {
      const data = await response.json();
      if (data.current_model) {
        // Model loaded and ready
        indicator.className = 'status-dot connected';
        text.textContent = `Ready (${data.current_model})`;
        messageInput.disabled = false;
        sendButton.disabled = false;
        isConnected = true;
      } else {
        // Server running but no model loaded
        indicator.className = 'status-dot warning';
        text.textContent = 'Server running, loading model...';
        messageInput.disabled = true;
        sendButton.disabled = true;
        isConnected = false;
      }
    } else {
      throw new Error('Server not responding');
    }
  } catch (error) {
    indicator.className = 'status-dot disconnected';
    text.textContent = 'Disconnected - Server starting...';
    messageInput.disabled = true;
    sendButton.disabled = true;
    isConnected = false;
  }
}

// Listen for setup status updates from Electron
if (typeof require !== 'undefined') {
  const { ipcRenderer } = require('electron');

  ipcRenderer.on('setup-status', (event, status) => {
    console.log('[Setup]:', status);

    // Show setup status in connection indicator
    const indicator = document.getElementById('connection-indicator');
    const text = document.getElementById('connection-text');

    if (indicator && text) {
      indicator.className = 'status-dot warning';
      text.textContent = status;
    }
  });
}

// Set up event listeners
document.addEventListener('DOMContentLoaded', () => {
  const loadModelBtn = document.getElementById('load-model-btn');
  if (loadModelBtn) {
    loadModelBtn.addEventListener('click', loadModel);
  }

  // Initial status check
  checkServerStatus();
  refreshModelsList();
  checkChatConnection();

  // Check connection status every 2 seconds
  connectionCheckInterval = setInterval(checkChatConnection, 2000);
});
