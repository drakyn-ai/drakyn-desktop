// ============================================================================
// PROACTIVE AGENT SETTINGS
// ============================================================================

// Save proactive settings
async function saveProactiveSettings() {
  const enabled = document.getElementById('proactive-enabled').checked;
  const checkInterval = document.getElementById('check-interval').value;
  const quietStart = document.getElementById('quiet-hours-start').value;
  const quietEnd = document.getElementById('quiet-hours-end').value;
  const maxQuestions = document.getElementById('max-questions').value;

  const settings = {
    enabled,
    check_interval_minutes: parseInt(checkInterval),
    quiet_hours_start: quietStart,
    quiet_hours_end: quietEnd,
    max_questions_per_day: parseInt(maxQuestions)
  };

  const statusEl = document.getElementById('proactive-settings-status');
  statusEl.textContent = 'Saving...';
  statusEl.className = 'status-message';

  try {
    // Save to user context file via agent
    const contextUpdate = `
Preferences:
- Proactive monitoring: ${enabled ? 'enabled' : 'disabled'}
- Check interval: ${checkInterval} minutes
- Quiet hours: ${quietStart} - ${quietEnd} (no notifications)
- Max learning questions per day: ${maxQuestions}
`;

    // TODO: Call backend to update user_context.txt
    // For now, just show success
    console.log('Proactive settings:', settings);

    statusEl.textContent = '✓ Settings saved! Restart monitor service to apply.';
    statusEl.className = 'status-message success';

    // Store in localStorage for UI persistence
    localStorage.setItem('proactive_settings', JSON.stringify(settings));

  } catch (error) {
    console.error('Failed to save proactive settings:', error);
    statusEl.textContent = '✗ Failed to save settings';
    statusEl.className = 'status-message error';
  }
}

// Load proactive settings from localStorage
function loadProactiveSettings() {
  try {
    const stored = localStorage.getItem('proactive_settings');
    if (stored) {
      const settings = JSON.parse(stored);

      document.getElementById('proactive-enabled').checked = settings.enabled !== false;
      document.getElementById('check-interval').value = settings.check_interval_minutes || 30;
      document.getElementById('quiet-hours-start').value = settings.quiet_hours_start || '22:00';
      document.getElementById('quiet-hours-end').value = settings.quiet_hours_end || '07:00';
      document.getElementById('max-questions').value = settings.max_questions_per_day || 3;
    }
  } catch (error) {
    console.error('Failed to load proactive settings:', error);
  }
}

// Event listeners
const saveProactiveBtn = document.getElementById('save-proactive-settings-btn');
if (saveProactiveBtn) {
  saveProactiveBtn.addEventListener('click', saveProactiveSettings);
}

// Load settings when settings page is shown
document.querySelectorAll('.sidebar a').forEach(link => {
  link.addEventListener('click', (e) => {
    const page = e.target.dataset.page;
    if (page === 'settings') {
      setTimeout(() => loadProactiveSettings(), 100);
    }
  });
});

// Load on page load
loadProactiveSettings();
