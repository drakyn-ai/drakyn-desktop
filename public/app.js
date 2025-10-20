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
      updateModelsPageForEngine();
      // Delay the refresh to ensure page is loaded
      setTimeout(() => refreshAvailableModels(), 500);
    }

    // Load settings when switching to settings page
    if (page === 'settings') {
      loadSettings();
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

  // Disable input while processing
  messageInput.disabled = true;
  sendButton.disabled = true;

  // Create agent message container
  const agentMessageDiv = document.createElement('div');
  agentMessageDiv.style.padding = '0.5rem';
  agentMessageDiv.style.marginBottom = '0.5rem';
  agentMessageDiv.style.backgroundColor = '#1e1e1e';
  agentMessageDiv.style.borderRadius = '4px';
  agentMessageDiv.style.borderLeft = '3px solid #858585';
  chatMessages.appendChild(agentMessageDiv);

  try {
    const response = await fetch(`${API_BASE_URL}/v1/agent/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: message,
        stream: true
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    // Read SSE stream
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let finalAnswer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop(); // Keep incomplete line in buffer

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = JSON.parse(line.slice(6));

          if (data.type === 'thinking') {
            agentMessageDiv.innerHTML = `<em style="color: #858585;">Thinking (iteration ${data.iteration + 1})...</em>`;
            if (data.content) {
              agentMessageDiv.innerHTML += `<br><div style="color: #858585; font-size: 0.9em; margin-top: 0.5rem; white-space: pre-wrap;">${data.content}</div>`;
            }
          } else if (data.type === 'tool_call') {
            agentMessageDiv.innerHTML = `<em style="color: #dcdcaa;">Calling tool: ${data.tool_name}</em>`;
            if (data.content) {
              agentMessageDiv.innerHTML += `<br><em style="color: #858585;">Reasoning: ${data.content}</em>`;
            }
            agentMessageDiv.innerHTML += `<br><code style="font-size: 0.85em; display: block; margin-top: 0.5rem;">${JSON.stringify(data.tool_args, null, 2)}</code>`;
          } else if (data.type === 'tool_result') {
            agentMessageDiv.innerHTML += `<br><em style="color: #4ec9b0;">Tool result received</em>`;
          } else if (data.type === 'answer') {
            finalAnswer = data.content;
            agentMessageDiv.innerHTML = `<strong>Agent:</strong> ${data.content}`;
          } else if (data.type === 'error') {
            agentMessageDiv.innerHTML = `<strong style="color: #f48771;">Error:</strong> ${data.error}`;
          } else if (data.type === 'done') {
            // Stream complete
            break;
          }

          chatMessages.scrollTop = chatMessages.scrollHeight;
        }
      }
    }

  } catch (error) {
    agentMessageDiv.innerHTML = `<strong style="color: #f48771;">Connection error:</strong> ${error.message}. Make sure a model is loaded.`;
  } finally {
    // Re-enable input
    messageInput.disabled = false;
    sendButton.disabled = false;
    messageInput.focus();
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

async function updateModelsPageForEngine() {
  const vllmOptions = document.getElementById('vllm-options-section');
  const modelHelpText = document.getElementById('model-help-text');
  const modelSectionTitle = document.getElementById('model-section-title');

  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    if (response.ok) {
      const data = await response.json();

      if (data.inference_engine === 'openai_compatible') {
        // Hide vLLM-specific options
        vllmOptions.style.display = 'none';
        modelSectionTitle.textContent = 'Select Model';
        modelHelpText.textContent = 'Choose a model available on your Ollama server';
      } else {
        // Show vLLM options
        vllmOptions.style.display = 'block';
        modelSectionTitle.textContent = 'Load a Model';
        modelHelpText.textContent = 'Enter a HuggingFace model name or local path';
      }
    }
  } catch (error) {
    console.log('Could not check engine type:', error);
  }
}

async function refreshAvailableModels() {
  const availableGroup = document.getElementById('available-models-group');
  const refreshBtn = document.getElementById('refresh-models-btn');

  if (!refreshBtn) return; // Button not on page yet

  refreshBtn.disabled = true;
  refreshBtn.textContent = 'Checking...';

  try {
    // Fetch available models through our Python server (which can access Ollama)
    const response = await fetch(`${API_BASE_URL}/available_models`);
    if (response.ok) {
      const data = await response.json();
      const models = data.models || [];

      // Clear existing options
      availableGroup.innerHTML = '';

      if (models.length > 0) {
        models.forEach(model => {
          const modelId = model.id || model.name;
          const option = document.createElement('option');
          option.value = modelId;
          option.textContent = `${modelId} ✓ (Downloaded)`;
          availableGroup.appendChild(option);
        });
        availableGroup.style.display = 'block';
      }
    } else {
      const errorData = await response.json();
      console.log('Could not fetch models:', errorData.detail);
    }
  } catch (error) {
    console.log('Could not fetch models from server:', error);
  } finally {
    refreshBtn.disabled = false;
    refreshBtn.textContent = 'Refresh Available Models';
  }
}

async function loadModel() {
  const dropdown = document.getElementById('model-dropdown');
  const modelPathInput = document.getElementById('model-path');
  const gpuMemory = parseFloat(document.getElementById('gpu-memory').value);
  const tensorParallel = parseInt(document.getElementById('tensor-parallel').value);
  const statusEl = document.getElementById('load-status');
  const loadBtn = document.getElementById('load-model-btn');

  // Get model from dropdown or text input
  let modelPath = dropdown.value || modelPathInput.value.trim();

  if (!modelPath) {
    statusEl.textContent = 'Please select or enter a model name';
    statusEl.style.color = '#f48771';
    return;
  }

  loadBtn.disabled = true;
  statusEl.textContent = 'Setting model...';
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

      if (data.inference_engine === 'openai_compatible') {
        // OpenAI-compatible mode
        if (data.current_model) {
          // Model is set and ready
          indicator.className = 'status-dot connected';
          text.textContent = `Ready (External: ${data.current_model})`;
          messageInput.disabled = false;
          sendButton.disabled = false;
          isConnected = true;
        } else {
          // No model set yet - need to "load" (which just sets the model name)
          indicator.className = 'status-dot warning';
          text.textContent = 'Ready - Set a model name in Models tab';
          messageInput.disabled = true;
          sendButton.disabled = true;
          isConnected = false;
        }
      } else {
        // vLLM mode
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
if (typeof window.electron !== 'undefined') {
  const { ipcRenderer } = window.electron;

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

// Settings functionality
async function loadSettings() {
  const engineSelect = document.getElementById('engine-select');
  const openaiUrlInput = document.getElementById('openai-url');
  const openaiUrlGroup = document.getElementById('openai-url-group');
  const currentConfigDiv = document.getElementById('current-config');

  // Try to get config from Electron IPC first (works even if server is down)
  if (typeof window.electron !== 'undefined') {
    try {
      const { ipcRenderer } = window.electron;
      const config = await ipcRenderer.invoke('get-config');

      engineSelect.value = config.inference_engine;
      openaiUrlInput.value = config.openai_compatible_url;

      if (config.inference_engine === 'openai_compatible') {
        openaiUrlGroup.style.display = 'block';
      }

      currentConfigDiv.innerHTML = `
        <p><strong>Engine:</strong> ${config.inference_engine}</p>
        ${config.inference_engine === 'openai_compatible' ? `<p><strong>External Server:</strong> ${config.openai_compatible_url}</p>` : ''}
        <p style="color: #858585;">Checking server status...</p>
      `;
    } catch (error) {
      console.error('Failed to load config from Electron:', error);
    }
  }

  // Try to get info from Python inference server
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    if (response.ok) {
      const data = await response.json();

      currentConfigDiv.innerHTML = `
        <p><strong>Engine:</strong> ${data.inference_engine || 'vllm'}</p>
        ${data.openai_compatible_url ? `<p><strong>External Server:</strong> ${data.openai_compatible_url}</p>` : ''}
        <p><strong>Current Model:</strong> ${data.current_model || 'None'}</p>
        <p style="color: #4ec9b0;">Python server is running</p>
      `;
    }
  } catch (error) {
    // Server not running
    const currentText = currentConfigDiv.innerHTML;
    if (!currentText.includes('running')) {
      currentConfigDiv.innerHTML = currentConfigDiv.innerHTML.replace('Checking server status...', '<span style="color: #858585;">Python server is starting...</span>');
    }
  }

  // Handle engine selection change
  engineSelect.addEventListener('change', () => {
    const openaiUrlGroup = document.getElementById('openai-url-group');
    if (engineSelect.value === 'openai_compatible') {
      openaiUrlGroup.style.display = 'block';
    } else {
      openaiUrlGroup.style.display = 'none';
    }
  });

  // Update server status
  updateServerStatus();
}

async function saveSettings() {
  const engineSelect = document.getElementById('engine-select');
  const openaiUrlInput = document.getElementById('openai-url');
  const statusEl = document.getElementById('settings-status');

  const engine = engineSelect.value;
  const url = openaiUrlInput.value.trim();

  if (engine === 'openai_compatible' && !url) {
    statusEl.textContent = 'Please enter an OpenAI-compatible server URL';
    statusEl.style.color = '#f48771';
    return;
  }

  // Update .env file via Electron IPC (works even if server is down)
  if (typeof window.electron !== 'undefined') {
    try {
      statusEl.textContent = 'Saving settings...';
      statusEl.style.color = '#dcdcaa';

      const { ipcRenderer } = window.electron;
      const result = await ipcRenderer.invoke('update-config', {
        inference_engine: engine,
        openai_compatible_url: url
      });

      if (result.success) {
        statusEl.textContent = 'Settings saved! Restart the server for changes to take effect.';
        statusEl.style.color = '#4ec9b0';
        // Refresh the config display
        setTimeout(() => loadSettings(), 500);
      } else {
        statusEl.textContent = `Failed to save: ${result.error}`;
        statusEl.style.color = '#f48771';
      }
    } catch (error) {
      statusEl.textContent = `Error saving settings: ${error.message}`;
      statusEl.style.color = '#f48771';
    }
  } else {
    statusEl.textContent = 'Settings can only be saved in Electron app';
    statusEl.style.color = '#f48771';
  }
}

async function updateServerStatus() {
  const statusText = document.getElementById('server-status-text');

  if (typeof window.electron !== 'undefined') {
    try {
      const { ipcRenderer } = window.electron;
      const status = await ipcRenderer.invoke('get-server-status');

      if (status.inference) {
        statusText.textContent = 'Running';
        statusText.style.color = '#4ec9b0';
      } else {
        statusText.textContent = 'Stopped';
        statusText.style.color = '#858585';
      }
    } catch (error) {
      statusText.textContent = 'Unknown';
      statusText.style.color = '#f48771';
    }
  }
}

async function startServer() {
  const statusEl = document.getElementById('server-control-status');

  if (typeof window.electron !== 'undefined') {
    try {
      statusEl.textContent = 'Starting server...';
      statusEl.style.color = '#dcdcaa';

      const { ipcRenderer } = window.electron;
      const result = await ipcRenderer.invoke('start-inference-server');

      if (result.success) {
        statusEl.textContent = 'Server started!';
        statusEl.style.color = '#4ec9b0';
        updateServerStatus();
      } else {
        statusEl.textContent = `Failed: ${result.message || result.error}`;
        statusEl.style.color = '#f48771';
      }
    } catch (error) {
      statusEl.textContent = `Error: ${error.message}`;
      statusEl.style.color = '#f48771';
    }
  }
}

async function stopServer() {
  const statusEl = document.getElementById('server-control-status');

  if (typeof window.electron !== 'undefined') {
    try {
      statusEl.textContent = 'Stopping server...';
      statusEl.style.color = '#dcdcaa';

      const { ipcRenderer } = window.electron;
      const result = await ipcRenderer.invoke('stop-inference-server');

      if (result.success) {
        statusEl.textContent = 'Server stopped!';
        statusEl.style.color = '#4ec9b0';
        updateServerStatus();
      } else {
        statusEl.textContent = `Failed: ${result.message || result.error}`;
        statusEl.style.color = '#f48771';
      }
    } catch (error) {
      statusEl.textContent = `Error: ${error.message}`;
      statusEl.style.color = '#f48771';
    }
  }
}

// Set up event listeners
document.addEventListener('DOMContentLoaded', () => {
  const loadModelBtn = document.getElementById('load-model-btn');
  if (loadModelBtn) {
    loadModelBtn.addEventListener('click', loadModel);
  }

  const refreshModelsBtn = document.getElementById('refresh-models-btn');
  if (refreshModelsBtn) {
    refreshModelsBtn.addEventListener('click', refreshAvailableModels);
  }

  const saveSettingsBtn = document.getElementById('save-settings-btn');
  if (saveSettingsBtn) {
    saveSettingsBtn.addEventListener('click', saveSettings);
  }

  const startServerBtn = document.getElementById('start-server-btn');
  if (startServerBtn) {
    startServerBtn.addEventListener('click', startServer);
  }

  const stopServerBtn = document.getElementById('stop-server-btn');
  if (stopServerBtn) {
    stopServerBtn.addEventListener('click', stopServer);
  }

  // Initial status check
  checkServerStatus();
  refreshModelsList();
  checkChatConnection();

  // Check connection status every 2 seconds
  connectionCheckInterval = setInterval(checkChatConnection, 2000);
});
