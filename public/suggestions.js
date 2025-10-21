// ============================================================================
// PROACTIVE SUGGESTIONS
// ============================================================================

let pendingSuggestions = [];

// Listen for proactive suggestions from Electron
window.electronAPI.receive('proactive-suggestion', (data) => {
  console.log('Received proactive suggestion:', data);

  // Add to pending list
  const suggestion = {
    id: Date.now().toString(),
    action: data.body || data.action || 'No action specified',
    reasoning: data.data?.reasoning || '',
    timestamp: new Date().toISOString(),
    status: 'pending'
  };

  pendingSuggestions.push(suggestion);
  updateSuggestionBadge();
  renderSuggestions();

  // Auto-show panel
  showSuggestionPanel();
});

// Listen for new suggestions
window.electronAPI.receive('new-suggestion', (suggestion) => {
  console.log('Received new suggestion:', suggestion);

  const item = {
    id: Date.now().toString(),
    action: suggestion.action || 'No action',
    reasoning: suggestion.reasoning || '',
    timestamp: new Date().toISOString(),
    status: 'pending'
  };

  pendingSuggestions.push(item);
  updateSuggestionBadge();
  renderSuggestions();
  showSuggestionPanel();
});

function updateSuggestionBadge() {
  const badge = document.getElementById('suggestion-badge');
  const count = document.getElementById('suggestion-count');
  const pending = pendingSuggestions.filter(s => s.status === 'pending');

  if (pending.length > 0) {
    count.textContent = pending.length;
    badge.style.display = 'block';
  } else {
    badge.style.display = 'none';
  }
}

function showSuggestionPanel() {
  const panel = document.getElementById('suggestion-panel');
  panel.style.display = 'flex';
  renderSuggestions();
}

function hideSuggestionPanel() {
  const panel = document.getElementById('suggestion-panel');
  panel.style.display = 'none';
}

function renderSuggestions() {
  const list = document.getElementById('suggestion-list');

  if (pendingSuggestions.length === 0) {
    list.innerHTML = '<div style="padding: 32px; text-align: center; color: #9ca3af;">No suggestions yet</div>';
    return;
  }

  // Render most recent first
  const sorted = [...pendingSuggestions].reverse();

  list.innerHTML = sorted.map(suggestion => {
    const time = new Date(suggestion.timestamp).toLocaleTimeString();
    const handled = suggestion.status !== 'pending';

    return `
      <div class="suggestion-item ${handled ? 'handled' : ''}" data-id="${suggestion.id}">
        <div class="suggestion-action">${escapeHtml(suggestion.action)}</div>
        ${suggestion.reasoning ? `<div class="suggestion-reasoning">${escapeHtml(suggestion.reasoning)}</div>` : ''}
        <div class="suggestion-time">${time}</div>
        ${handled ? `
          <div class="suggestion-status status-${suggestion.status}">
            ${suggestion.status === 'accepted' ? '✓ Accepted' : '✗ Dismissed'}
          </div>
        ` : `
          <div class="suggestion-buttons">
            <button class="btn-accept" onclick="handleSuggestion('${suggestion.id}', 'accepted')">
              ✓ Accept
            </button>
            <button class="btn-dismiss" onclick="handleSuggestion('${suggestion.id}', 'dismissed')">
              ✗ Dismiss
            </button>
          </div>
        `}
      </div>
    `;
  }).join('');
}

function handleSuggestion(suggestionId, action) {
  const suggestion = pendingSuggestions.find(s => s.id === suggestionId);
  if (!suggestion) return;

  suggestion.status = action;

  // Send to backend for logging
  console.log(`Suggestion ${action}:`, suggestion);

  // Update UI
  updateSuggestionBadge();
  renderSuggestions();

  // TODO: Send to Python service to record in suggestion_history.txt
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Event listeners
document.getElementById('suggestion-badge')?.addEventListener('click', showSuggestionPanel);
document.getElementById('close-suggestions')?.addEventListener('click', hideSuggestionPanel);

// Initialize
updateSuggestionBadge();
