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

    if (page === 'projects') {
      renderProjectList();
      showProjectDetail(getProjectById(activeProjectId));
    }

    if (page === 'capabilities') {
      renderCapabilities();
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

const projectListEl = document.getElementById('project-list');
const newProjectBtn = document.getElementById('new-project-btn');
const quickNewProjectBtn = document.getElementById('quick-new-project-btn');
const projectStatusSelect = document.getElementById('project-status-select');
const activeProjectSelect = document.getElementById('active-project-select');
const activeProjectTitle = document.getElementById('active-project-title');
const activeProjectSummary = document.getElementById('active-project-summary');
const activeProjectStatus = document.getElementById('active-project-status');
const activeProjectActivity = document.getElementById('active-project-activity');
const projectDetailContainer = document.getElementById('project-detail');
const projectDetailEmpty = document.getElementById('project-detail-empty');
const projectDetailUpdatedEl = document.getElementById('project-detail-updated');
const chatProjectSummaryEl = document.getElementById('chat-project-summary');
const chatProjectStatusEl = document.getElementById('chat-project-status');
const chatProjectUpdatedEl = document.getElementById('chat-project-updated');

const markdownAvailable = typeof marked !== 'undefined';

if (markdownAvailable) {
  marked.setOptions({
    breaks: true,
    gfm: true,
    headerIds: false,
    mangle: false
  });
}

const renderMarkdown = (text) => {
  if (!markdownAvailable || typeof DOMPurify === 'undefined') {
    return null;
  }

  const rawHtml = marked.parse(text == null ? '' : text);
  return DOMPurify.sanitize(rawHtml, { USE_PROFILES: { html: true } });
};

const escapeHtml = (str = '') => String(str)
  .replace(/&/g, '&amp;')
  .replace(/</g, '&lt;')
  .replace(/>/g, '&gt;')
  .replace(/"/g, '&quot;')
  .replace(/'/g, '&#39;');

const PROJECT_STATUS_META = {
  planning: { label: 'Planning', icon: '🧭', modifier: 'planning' },
  researching: { label: 'Researching', icon: '🔍', modifier: 'researching' },
  building: { label: 'Building', icon: '💡', modifier: 'building' },
  review: { label: 'Review', icon: '📝', modifier: 'review' },
  complete: { label: 'Complete', icon: '✅', modifier: 'complete' }
};

const PROJECT_STATUS_SEQUENCE = ['planning', 'researching', 'building', 'review', 'complete'];

const createProjectId = () => `project-${Math.random().toString(36).slice(2, 10)}`;

const formatRelativeTime = (timestamp) => {
  if (!timestamp) return 'Just now';

  const diff = Date.now() - timestamp;
  if (diff < 60000) return 'Just now';
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
  const days = Math.floor(diff / 86400000);
  return `${days}d ago`;
};

const seedNow = Date.now();
const projects = [
  {
    id: createProjectId(),
    name: 'Personal HQ',
    summary: 'Capture anything you want Drakyn to drive without leaving your desktop.',
    status: 'planning',
    lastUpdated: seedNow,
    activity: 'Ready when you are.'
  }
];

const projectConversations = new Map();
let activeProjectId = projects.length ? projects[0].id : null;

// Capabilities System
const CAPABILITIES = [
  // Core (Always Available)
  {
    id: 'conversation',
    title: 'Natural Conversation',
    description: 'Chat naturally with an AI that understands context and remembers your preferences',
    category: 'core',
    icon: '💬',
    unlocked: true,
    examples: [
      'Help me brainstorm ideas for a project',
      'Explain this concept to me',
      'Answer questions about any topic'
    ]
  },
  {
    id: 'project-management',
    title: 'Project Tracking',
    description: 'Organize work into projects with intelligent status tracking and progress monitoring',
    category: 'core',
    icon: '📋',
    unlocked: true,
    examples: [
      'Create a project to plan my birthday party',
      'Track progress on my home renovation',
      'Get status updates on all my projects'
    ]
  },
  {
    id: 'file-search',
    title: 'Local File Search',
    description: 'Search and find files on your computer using natural language',
    category: 'core',
    icon: '📁',
    unlocked: true,
    examples: [
      'Find all PDFs from last month',
      'Search for documents about [topic]',
      'Locate files modified this week'
    ]
  },
  {
    id: 'web-search',
    title: 'Web Research',
    description: 'Search the internet and get summarized, relevant information',
    category: 'core',
    icon: '🔍',
    unlocked: true,
    examples: [
      'Research gift ideas for a 2-year-old',
      'Find the best restaurants in my area',
      'Look up current news on [topic]'
    ]
  },
  {
    id: 'memory',
    title: 'Personal Memory',
    description: 'Remember information about you, your preferences, and your life for personalized assistance',
    category: 'core',
    icon: '🧠',
    unlocked: true,
    examples: [
      'Remember I prefer mornings for focused work',
      'Note that I have meetings every Tuesday',
      'Store my dietary preferences'
    ]
  },

  // Email (Requires Gmail Connection)
  {
    id: 'email-management',
    title: 'Email Management',
    description: 'Read, search, organize, and respond to your emails intelligently',
    category: 'email',
    icon: '📧',
    unlocked: false,
    requiresSetup: 'gmail',
    setupInstructions: 'Connect your Gmail account to unlock email capabilities',
    examples: [
      'Show me unread emails from this week',
      'Find emails about [topic] from [person]',
      'Draft a professional response to my last email',
      'Archive all newsletters from last month'
    ]
  },

  // Calendar (Requires Calendar Connection)
  {
    id: 'calendar-scheduling',
    title: 'Calendar & Scheduling',
    description: 'View your schedule, find meeting times, and manage your calendar',
    category: 'calendar',
    icon: '🗓️',
    unlocked: false,
    requiresSetup: 'calendar',
    setupInstructions: 'Connect your calendar to unlock scheduling capabilities',
    examples: [
      'What\'s on my schedule today?',
      'Find a 30-minute slot to meet with John',
      'Add a reminder for tomorrow at 2pm',
      'Show me all meetings this week'
    ]
  },

  // Slack (Requires Slack Integration)
  {
    id: 'slack-integration',
    title: 'Slack Communication',
    description: 'Read messages, send updates, and manage Slack channels',
    category: 'communication',
    icon: '💬',
    unlocked: false,
    requiresSetup: 'slack',
    setupInstructions: 'Install Slack MCP server to unlock team communication',
    examples: [
      'Send a message to #general channel',
      'Check for new Slack messages',
      'Post an update about project progress'
    ]
  },

  // GitHub (Requires GitHub Integration)
  {
    id: 'github-integration',
    title: 'GitHub Management',
    description: 'Manage repositories, create issues, review pull requests, and track development',
    category: 'development',
    icon: '🐙',
    unlocked: false,
    requiresSetup: 'github',
    setupInstructions: 'Install GitHub MCP server to unlock code management',
    examples: [
      'Create an issue for bug tracking',
      'Review open pull requests',
      'Check repository status',
      'List recent commits'
    ]
  },

  // Notion (Requires Notion Integration)
  {
    id: 'notion-integration',
    title: 'Notion Workspace',
    description: 'Access and update your Notion pages, databases, and knowledge base',
    category: 'productivity',
    icon: '📝',
    unlocked: false,
    requiresSetup: 'notion',
    setupInstructions: 'Install Notion MCP server to unlock your workspace',
    examples: [
      'Add a note to my personal wiki',
      'Search my Notion database',
      'Update project documentation',
      'Create a new page in my workspace'
    ]
  },

  // Cloud Storage (Requires Dropbox/Google Drive)
  {
    id: 'cloud-storage',
    title: 'Cloud File Access',
    description: 'Access files from Dropbox, Google Drive, and other cloud storage',
    category: 'files',
    icon: '☁️',
    unlocked: false,
    requiresSetup: 'cloud',
    setupInstructions: 'Connect cloud storage to access files anywhere',
    examples: [
      'Find documents in my Google Drive',
      'Search for images in Dropbox',
      'Access shared folder contents'
    ]
  },

  // Advanced Automation
  {
    id: 'automation',
    title: 'Workflow Automation',
    description: 'Set up recurring tasks, scheduled checks, and automated workflows',
    category: 'automation',
    icon: '⚙️',
    unlocked: true,
    advanced: true,
    examples: [
      'Every Monday, summarize my unread emails',
      'Check project status weekly',
      'Remind me to follow up on pending tasks'
    ]
  }
];

const getProjectById = (id) => projects.find(project => project.id === id);

const ensureProjectConversation = (projectId) => {
  if (!projectConversations.has(projectId)) {
    const container = document.createElement('div');
    container.className = 'project-conversation';
    projectConversations.set(projectId, container);
  }
  return projectConversations.get(projectId);
};

const getStatusMeta = (statusKey) => PROJECT_STATUS_META[statusKey] || PROJECT_STATUS_META.planning;

const applyStatusPill = (element, baseClass, statusKey) => {
  if (!element) return;
  const meta = getStatusMeta(statusKey);
  const classes = [];
  if (baseClass) classes.push(baseClass);
  classes.push('status-pill');
  if (meta.modifier) classes.push(meta.modifier);
  element.className = classes.join(' ');
  element.textContent = `${meta.icon} ${meta.label}`;
};

const updateProjectSelectOptions = () => {
  if (!activeProjectSelect) return;

  activeProjectSelect.innerHTML = '';

  if (projects.length === 0) {
    const option = document.createElement('option');
    option.value = '';
    option.textContent = 'No projects yet';
    activeProjectSelect.appendChild(option);
    activeProjectSelect.disabled = true;
    return;
  }

  activeProjectSelect.disabled = false;
  const sortedProjects = [...projects].sort((a, b) => b.lastUpdated - a.lastUpdated);
  sortedProjects.forEach(project => {
    const option = document.createElement('option');
    option.value = project.id;
    option.textContent = project.name;
    activeProjectSelect.appendChild(option);
  });

  if (activeProjectId) {
    activeProjectSelect.value = activeProjectId;
  }
};

function updateChatProjectMeta(project) {
  if (!chatProjectSummaryEl || !chatProjectStatusEl || !chatProjectUpdatedEl) return;

  if (!project) {
    chatProjectSummaryEl.textContent = 'Let Drakyn know what matters and it will keep everything organized for you.';
    applyStatusPill(chatProjectStatusEl, '', 'planning');
    chatProjectUpdatedEl.textContent = 'No project selected';
    return;
  }

  chatProjectSummaryEl.textContent = project.summary || 'No summary yet — add a quick description in the Projects tab.';
  applyStatusPill(chatProjectStatusEl, '', project.status);
  chatProjectUpdatedEl.textContent = `Updated ${formatRelativeTime(project.lastUpdated)}`;
}

function showProjectDetail(project) {
  if (!projectDetailContainer || !projectDetailEmpty) return;

  if (!project) {
    projectDetailContainer.style.display = 'none';
    projectDetailEmpty.style.display = 'flex';
    return;
  }

  projectDetailEmpty.style.display = 'none';
  projectDetailContainer.style.display = 'block';

  if (activeProjectTitle) {
    activeProjectTitle.textContent = project.name;
  }

  if (activeProjectSummary) {
    activeProjectSummary.textContent = project.summary;
  }

  applyStatusPill(activeProjectStatus, 'active-project-status', project.status);

  if (activeProjectActivity) {
    activeProjectActivity.textContent = project.activity || 'No updates yet — Drakyn is ready when you are.';
  }

  if (projectDetailUpdatedEl) {
    projectDetailUpdatedEl.textContent = `Updated ${formatRelativeTime(project.lastUpdated)}`;
  }

  if (projectStatusSelect) {
    projectStatusSelect.innerHTML = '';
    PROJECT_STATUS_SEQUENCE.forEach(statusKey => {
      const option = document.createElement('option');
      option.value = statusKey;
      option.textContent = PROJECT_STATUS_META[statusKey].label;
      if (statusKey === project.status) {
        option.selected = true;
      }
      projectStatusSelect.appendChild(option);
    });
  }

  // Show agent assessment if available
  const assessmentContainer = document.getElementById('project-agent-assessment');
  if (assessmentContainer && project.agent_status) {
    assessmentContainer.style.display = 'block';

    // Update status badge
    const statusBadge = document.getElementById('agent-status-badge');
    if (statusBadge) {
      const statusMap = {
        'on_track': { label: '✅ On Track', class: 'on-track' },
        'blocked': { label: '🚫 Blocked', class: 'blocked' },
        'needs_info': { label: '❓ Needs Info', class: 'needs-info' },
        'at_risk': { label: '⚠️ At Risk', class: 'at-risk' },
        'complete': { label: '🎉 Complete', class: 'complete' }
      };
      const status = statusMap[project.agent_status] || statusMap['on_track'];
      statusBadge.textContent = status.label;
      statusBadge.className = `agent-status-badge ${status.class}`;
    }

    // Update estimated completion
    const estimatedEl = document.getElementById('estimated-completion');
    if (estimatedEl && project.estimated_completion) {
      estimatedEl.textContent = `Est: ${project.estimated_completion}`;
      estimatedEl.style.display = 'inline-block';
    }

    // Update agent summary
    const summaryEl = document.getElementById('agent-summary');
    if (summaryEl && project.agent_summary) {
      summaryEl.textContent = project.agent_summary;
    }

    // Update blockers if any
    const blockersSection = document.getElementById('blockers-section');
    const blockersText = document.getElementById('blockers-text');
    if (blockersSection && blockersText && project.blockers && project.blockers !== 'None identified') {
      blockersSection.style.display = 'block';
      blockersText.textContent = project.blockers;
    } else if (blockersSection) {
      blockersSection.style.display = 'none';
    }
  } else if (assessmentContainer) {
    assessmentContainer.style.display = 'none';
  }
}

function renderProjectList() {
  if (!projectListEl) return;

  const previousScroll = projectListEl.scrollTop;
  projectListEl.innerHTML = '';

  if (projects.length === 0) {
    const emptyState = document.createElement('div');
    emptyState.className = 'project-empty-state';
    emptyState.innerHTML = `
      <h4>No projects yet</h4>
      <p>Spin up a dedicated workspace and Drakyn will keep everything organized for you.</p>
    `;
    projectListEl.appendChild(emptyState);
    updateProjectSelectOptions();
    return;
  }

  const sortedProjects = [...projects].sort((a, b) => b.lastUpdated - a.lastUpdated);

  sortedProjects.forEach(project => {
    const item = document.createElement('button');
    item.type = 'button';
    item.className = 'project-item';
    item.dataset.projectId = project.id;
    if (project.id === activeProjectId) {
      item.classList.add('active');
    }

    const header = document.createElement('div');
    header.className = 'project-item-header';

    const nameEl = document.createElement('span');
    nameEl.className = 'project-item-name';
    nameEl.textContent = project.name;
    header.appendChild(nameEl);

    const statusBadge = document.createElement('span');
    applyStatusPill(statusBadge, 'project-status-badge', project.status);
    header.appendChild(statusBadge);

    item.appendChild(header);

    const summary = document.createElement('p');
    summary.className = 'project-item-summary';
    summary.textContent = project.summary;
    item.appendChild(summary);

    const footer = document.createElement('div');
    footer.className = 'project-item-footer';

    const activity = document.createElement('span');
    activity.className = 'project-activity';
    activity.textContent = project.activity || 'Awaiting updates';
    footer.appendChild(activity);

    const timestamp = document.createElement('span');
    timestamp.className = 'project-timestamp';
    timestamp.textContent = formatRelativeTime(project.lastUpdated);
    footer.appendChild(timestamp);

    item.appendChild(footer);

    item.addEventListener('click', () => setActiveProject(project.id));
    projectListEl.appendChild(item);
  });

  projectListEl.scrollTop = previousScroll;
  updateProjectSelectOptions();
}

function setActiveProject(projectId, options = {}) {
  const project = getProjectById(projectId);
  if (!project) return;

  activeProjectId = projectId;

  const projectContainer = ensureProjectConversation(projectId);
  if (chatMessages.firstElementChild !== projectContainer) {
    chatMessages.innerHTML = '';
    chatMessages.appendChild(projectContainer);
  }
  chatMessages.scrollTop = projectContainer.scrollHeight;

  if (messageInput) {
    messageInput.placeholder = `Ask Drakyn about "${project.name}"...`;
  }

  updateChatProjectMeta(project);
  showProjectDetail(project);

  if (activeProjectSelect && !options.skipSelectUpdate) {
    activeProjectSelect.value = projectId;
  }

  if (!options.skipListUpdate) {
    renderProjectList();
  }
}

function updateProjectActivity(projectId, speaker, text) {
  const project = getProjectById(projectId);
  if (!project) return;

  const cleanSpeaker = speaker || 'Update';
  const cleanText = text ? String(text).trim() : '';
  const truncated = cleanText.length > 80 ? `${cleanText.slice(0, 77)}…` : cleanText;

  project.activity = truncated ? `${cleanSpeaker}: ${truncated}` : `${cleanSpeaker} shared an update`;
  project.lastUpdated = Date.now();

  if (projectId === activeProjectId) {
    if (activeProjectActivity) {
      activeProjectActivity.textContent = project.activity;
    }
    updateChatProjectMeta(project);
    showProjectDetail(project);
  }

  renderProjectList();
}

function handleProjectStatusChange(event) {
  const project = getProjectById(activeProjectId);
  if (!project) return;

  const nextStatus = event.target.value;
  if (PROJECT_STATUS_META[nextStatus]) {
    project.status = nextStatus;
  }

  project.lastUpdated = Date.now();

  updateChatProjectMeta(project);
  showProjectDetail(project);
  renderProjectList();
}

const createProject = ({ name, summary, status = 'planning', activity = 'Ready when you are.' } = {}) => {
  const newProject = {
    id: createProjectId(),
    name: name && name.trim() ? name.trim() : 'Untitled Project',
    summary: summary && summary.trim() ? summary.trim() : 'Outline the goals and guardrails for this initiative.',
    status: PROJECT_STATUS_META[status] ? status : 'planning',
    lastUpdated: Date.now(),
    activity: activity && activity.trim() ? activity.trim() : 'Ready when you are.'
  };

  projects.unshift(newProject);
  ensureProjectConversation(newProject.id);
  updateProjectSelectOptions();
  setActiveProject(newProject.id, { skipListUpdate: true, skipSelectUpdate: true });
  renderProjectList();
  if (activeProjectSelect) {
    activeProjectSelect.value = newProject.id;
  }
  updateChatProjectMeta(newProject);
  showProjectDetail(newProject);
  return newProject;
};

const handleNewProject = () => {
  const nameInput = prompt('What would you like to call this project?');
  if (nameInput === null) return;

  const summaryInput = prompt('How should Drakyn help you here?', 'Outline the goals and guardrails for this initiative.');
  createProject({
    name: nameInput,
    summary: summaryInput
  });
};

async function analyzeProjectStatus() {
  const project = getProjectById(activeProjectId);
  if (!project) {
    alert('No active project selected');
    return;
  }

  // Get the button to show loading state
  const analyzeBtn = document.getElementById('analyze-status-btn');
  if (analyzeBtn) {
    analyzeBtn.disabled = true;
    analyzeBtn.textContent = 'Analyzing...';
  }

  try {
    // Get current project context including conversation history
    const projectContainer = ensureProjectConversation(activeProjectId);
    const messages = Array.from(projectContainer.querySelectorAll('.chat-message'));
    const conversationSummary = messages.slice(-10).map(msg => {
      const role = msg.classList.contains('user-message') ? 'User' : 'Drakyn';
      const content = msg.querySelector('.message-content')?.textContent || '';
      return `${role}: ${content.substring(0, 200)}`;
    }).join('\n');

    // Build analysis prompt
    const analysisPrompt = `Please analyze the current status of this project and provide:
1. Status assessment (choose one: on_track, blocked, needs_info, at_risk, or complete)
2. A brief summary (1-2 sentences) of what's been done and what's next
3. Estimated time to completion (e.g., "2 days", "1 week", "unknown")
4. Any blockers preventing progress (or "None identified")

Project: ${project.name}
Summary: ${project.summary}
Current Status: ${project.status}

Recent conversation:
${conversationSummary}

Use the project_manager tool with action='analyze_status' to save your assessment.`;

    // Send analysis request to agent
    const response = await fetch(`${API_BASE_URL}/v1/agent/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: analysisPrompt,
        stream: false,
        project_context: {
          id: project.id,
          name: project.name,
          summary: project.summary,
          status: project.status
        }
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    console.log('[Analysis Response]', data);

    // The UI will be updated automatically through the update_project ui_action

  } catch (error) {
    console.error('Failed to analyze project status:', error);
    alert(`Failed to analyze project: ${error.message}`);
  } finally {
    // Reset button state
    if (analyzeBtn) {
      analyzeBtn.disabled = false;
      analyzeBtn.textContent = 'Update Status';
    }
  }
}

const initializeProjectWorkspace = () => {
  projects.forEach(project => ensureProjectConversation(project.id));

  if (!activeProjectId && projects.length) {
    activeProjectId = projects[0].id;
  }

  updateProjectSelectOptions();

  const initialProject = getProjectById(activeProjectId);
  if (initialProject) {
    setActiveProject(initialProject.id, { skipListUpdate: true, skipSelectUpdate: true });
    renderProjectList();
  } else {
    renderProjectList();
    updateChatProjectMeta(null);
    showProjectDetail(null);
  }

  if (newProjectBtn && !newProjectBtn.dataset.bound) {
    newProjectBtn.addEventListener('click', handleNewProject);
    newProjectBtn.dataset.bound = 'true';
  }

  if (quickNewProjectBtn && !quickNewProjectBtn.dataset.bound) {
    quickNewProjectBtn.addEventListener('click', handleNewProject);
    quickNewProjectBtn.dataset.bound = 'true';
  }

  if (projectStatusSelect && !projectStatusSelect.dataset.bound) {
    projectStatusSelect.addEventListener('change', handleProjectStatusChange);
    projectStatusSelect.dataset.bound = 'true';
  }

  if (activeProjectSelect && !activeProjectSelect.dataset.bound) {
    activeProjectSelect.addEventListener('change', (event) => {
      const nextProjectId = event.target.value;
      if (nextProjectId) {
        setActiveProject(nextProjectId);
      }
    });
    activeProjectSelect.dataset.bound = 'true';
  }
};

if (typeof window !== 'undefined') {
  window.DrakynProjects = {
    createProjectFromAgent: ({ name, summary, status, activity } = {}) => createProject({ name, summary, status, activity }),
    setActiveProject: (projectId) => setActiveProject(projectId),
    listProjects: () => projects.map(project => ({ ...project })),
    updateProjectActivity: (projectId, speaker, text) => updateProjectActivity(projectId, speaker, text)
  };
}

function addMessage(text, isUser = true, projectId = activeProjectId) {
  const fallbackProjectId = projects.length ? projects[0].id : null;
  const targetProjectId = projectId || activeProjectId || fallbackProjectId;
  if (!targetProjectId) {
    return { messageDiv: null, content: null };
  }

  if (targetProjectId !== activeProjectId) {
    setActiveProject(targetProjectId, { skipListUpdate: false, skipSelectUpdate: false });
  }

  const projectContainer = ensureProjectConversation(targetProjectId);

  const messageDiv = document.createElement('div');
  messageDiv.className = 'chat-message';
  messageDiv.classList.add(isUser ? 'user-message' : 'agent-message');

  // Create header with sender label
  const header = document.createElement('div');
  header.className = 'message-header';
  header.textContent = isUser ? 'You' : 'Drakyn';
  messageDiv.appendChild(header);

  // Create content div
  const content = document.createElement('div');
  content.className = 'message-content';

  // Render markdown for agent messages, plain text for user
  if (!isUser) {
    const renderedMarkdown = renderMarkdown(text);
    if (renderedMarkdown !== null) {
      content.innerHTML = renderedMarkdown;
    } else {
      content.textContent = text;
    }
  } else {
    content.textContent = text;
  }

  messageDiv.appendChild(content);
  projectContainer.appendChild(messageDiv);
  chatMessages.scrollTop = projectContainer.scrollHeight;

  return { messageDiv, content };
}

async function sendMessage() {
  const message = messageInput.value.trim();
  if (!message) return;

  addMessage(message, true, activeProjectId);
  updateProjectActivity(activeProjectId, 'You', message);
  messageInput.value = '';

  // Disable input while processing
  messageInput.disabled = true;
  sendButton.disabled = true;

  // Create agent message container
  const agentMessageDiv = document.createElement('div');
  agentMessageDiv.className = 'chat-message agent-message';

  // Create header
  const header = document.createElement('div');
  header.className = 'message-header';
  header.textContent = 'Drakyn';
  agentMessageDiv.appendChild(header);

  // Create content div
  const content = document.createElement('div');
  content.className = 'message-content';
  agentMessageDiv.appendChild(content);

  const projectContainer = ensureProjectConversation(activeProjectId);
  if (chatMessages.firstElementChild !== projectContainer) {
    chatMessages.innerHTML = '';
    chatMessages.appendChild(projectContainer);
  }
  projectContainer.appendChild(agentMessageDiv);

  try {
    // Get current project context
    const currentProject = getProjectById(activeProjectId);
    const projectContext = currentProject ? {
      id: currentProject.id,
      name: currentProject.name,
      summary: currentProject.summary,
      status: currentProject.status
    } : null;

    const response = await fetch(`${API_BASE_URL}/v1/agent/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: message,
        stream: true,
        project_context: projectContext
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
    let sawThinkingUpdate = false;
    let receivedAnswer = false;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop(); // Keep incomplete line in buffer

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = JSON.parse(line.slice(6));
          console.log('[Drakyn Step]', data);  // Debug logging

          if (data.type === 'thinking') {
            content.replaceChildren();

            const thinkingEm = document.createElement('em');
            thinkingEm.style.color = '#6a737d';
            thinkingEm.textContent = `Thinking (iteration ${data.iteration + 1})...`;
            content.appendChild(thinkingEm);
            sawThinkingUpdate = true;

            if (data.content) {
              const reasoningDiv = document.createElement('div');
              reasoningDiv.style.color = '#6a737d';
              reasoningDiv.style.fontSize = '0.9em';
              reasoningDiv.style.marginTop = '0.5rem';
              reasoningDiv.style.whiteSpace = 'pre-wrap';
              reasoningDiv.textContent = data.content;
              content.appendChild(reasoningDiv);
            }
          } else if (data.type === 'tool_call') {
            content.replaceChildren();

            const callEm = document.createElement('em');
            callEm.style.color = '#0366d6';
            callEm.textContent = `Calling tool: ${data.tool_name}`;
            content.appendChild(callEm);

            if (data.content) {
              const reasoningEm = document.createElement('em');
              reasoningEm.style.color = '#6a737d';
              reasoningEm.style.display = 'block';
              reasoningEm.style.marginTop = '0.5rem';
              reasoningEm.textContent = `Reasoning: ${data.content}`;
              content.appendChild(reasoningEm);
            }

            const argsJson = JSON.stringify(data.tool_args, null, 2);
            const argsFallback = (data.tool_args === null || data.tool_args === undefined) ? '' : data.tool_args;
            const argsText = argsJson !== undefined ? argsJson : String(argsFallback);
            const argsPre = document.createElement('pre');
            argsPre.style.marginTop = '0.5rem';
            const argsCode = document.createElement('code');
            argsCode.textContent = argsText;
            argsPre.appendChild(argsCode);
            content.appendChild(argsPre);
          } else if (data.type === 'tool_result') {
            const resultEm = document.createElement('em');
            resultEm.style.color = '#28a745';
            resultEm.style.display = 'block';
            resultEm.style.marginTop = '0.5rem';
            resultEm.textContent = 'Tool result received';
            content.appendChild(resultEm);
            // Log tool result for debugging
            if (data.result) {
              console.log('[Tool Result]', data.result);

              // Handle UI actions from tools
              if (data.result.ui_action) {
                const uiAction = data.result.ui_action;
                console.log('[UI Action]', uiAction);

                if (uiAction.type === 'create_project' && uiAction.project) {
                  // Create project in UI
                  const project = uiAction.project;
                  if (window.DrakynProjects && window.DrakynProjects.createProjectFromAgent) {
                    window.DrakynProjects.createProjectFromAgent({
                      name: project.name,
                      summary: project.summary,
                      status: project.status,
                      activity: project.activity
                    });
                    console.log('[UI] Created project in UI:', project.name);
                  }
                } else if (uiAction.type === 'update_project' && uiAction.project) {
                  // Update project in UI
                  const projectIndex = projects.findIndex(p => p.id === uiAction.project.id);
                  if (projectIndex !== -1) {
                    // Merge updated fields
                    projects[projectIndex] = { ...projects[projectIndex], ...uiAction.project };
                    console.log('[UI] Updated project in UI:', uiAction.project.name);

                    // Refresh UI
                    if (activeProjectId === uiAction.project.id) {
                      showProjectDetail(projects[projectIndex]);
                    }
                    renderProjectList();
                  }
                } else if (uiAction.type === 'delete_project' && uiAction.project_id) {
                  // Delete project from UI
                  const projectIndex = projects.findIndex(p => p.id === uiAction.project_id);
                  if (projectIndex !== -1) {
                    const deletedProject = projects[projectIndex];
                    projects.splice(projectIndex, 1);
                    console.log('[UI] Deleted project from UI:', deletedProject.name);

                    // Switch to new active project or first available
                    if (uiAction.new_active_project_id) {
                      setActiveProject(uiAction.new_active_project_id);
                    } else if (projects.length > 0) {
                      setActiveProject(projects[0].id);
                    } else {
                      // No projects left
                      activeProjectId = null;
                      updateProjectSelectOptions();
                      updateChatProjectMeta(null);
                      showProjectDetail(null);
                    }
                    renderProjectList();
                  }
                }
              }
            }
          } else if (data.type === 'answer') {
            finalAnswer = data.content == null ? '' : data.content;
            const renderedAnswer = renderMarkdown(finalAnswer);
            if (renderedAnswer !== null) {
              content.innerHTML = renderedAnswer;
            } else {
              content.textContent = finalAnswer;
            }
            receivedAnswer = receivedAnswer || finalAnswer.length > 0;
            updateProjectActivity(activeProjectId, 'Drakyn', finalAnswer);
          } else if (data.type === 'error') {
            const errorMessage = data.error == null ? 'Unknown error' : data.error;
            content.innerHTML = `<strong style="color: #dc3545;">Error:</strong> ${escapeHtml(errorMessage)}`;
            updateProjectActivity(activeProjectId, 'Drakyn', `Error: ${errorMessage}`);
          } else if (data.type === 'done') {
            // Stream complete
            console.log('[Drakyn] Stream complete, final answer:', finalAnswer);
            break;
          }

          chatMessages.scrollTop = projectContainer.scrollHeight;
        }
      }
    }

    // Check if we got any answer after stream completes
    if (!receivedAnswer && sawThinkingUpdate) {
      console.warn('[Drakyn] Stream ended but no final answer received');
      agentMessageDiv.innerHTML = `<strong style="color: #dc3545;">Error:</strong> Drakyn did not provide a response. Check server logs for details.`;
      updateProjectActivity(activeProjectId, 'Drakyn', 'No response produced — check server logs for details.');
    }

  } catch (error) {
    const errorMessage = error && error.message ? error.message : 'Unknown error';
    agentMessageDiv.innerHTML = `<strong style="color: #dc3545;">Connection error:</strong> ${escapeHtml(errorMessage)}. Make sure a model is loaded.`;
    updateProjectActivity(activeProjectId, 'Drakyn', `Connection error: ${errorMessage}`);
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

      // Save model selection to localStorage
      localStorage.setItem('lastModel', modelPath);
      localStorage.setItem('lastGpuMemory', gpuMemory);
      localStorage.setItem('lastTensorParallel', tensorParallel);

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

// Capabilities Dashboard
function renderCapabilities() {
  const capabilitiesGrid = document.getElementById('capabilities-grid');
  const unlockedCount = document.getElementById('capabilities-unlocked');
  const totalCount = document.getElementById('capabilities-total');

  if (!capabilitiesGrid) return;

  // Calculate unlocked count
  const unlocked = CAPABILITIES.filter(c => c.unlocked).length;
  const total = CAPABILITIES.length;

  // Update stats
  if (unlockedCount) unlockedCount.textContent = unlocked;
  if (totalCount) totalCount.textContent = total;

  // Clear existing cards
  capabilitiesGrid.innerHTML = '';

  // Render each capability card
  CAPABILITIES.forEach(capability => {
    const card = document.createElement('div');
    card.className = `capability-card ${capability.unlocked ? 'unlocked' : 'locked'}`;

    // Category badge
    const categoryColors = {
      'core': '#4ec9b0',
      'email': '#ce9178',
      'calendar': '#dcdcaa',
      'communication': '#569cd6',
      'development': '#4fc1ff',
      'productivity': '#c586c0',
      'files': '#9cdcfe',
      'automation': '#b5cea8'
    };

    const categoryColor = categoryColors[capability.category] || '#858585';

    card.innerHTML = `
      <div class="capability-header">
        <div class="capability-icon">${capability.icon}</div>
        <div class="capability-meta">
          <h3 class="capability-title">${capability.title}</h3>
          <span class="capability-category" style="background-color: ${categoryColor}20; color: ${categoryColor};">
            ${capability.category}
          </span>
        </div>
        ${capability.unlocked ?
          '<div class="capability-status unlocked-badge">✓ Unlocked</div>' :
          '<div class="capability-status locked-badge">🔒 Locked</div>'
        }
      </div>

      <p class="capability-description">${capability.description}</p>

      ${capability.unlocked ? `
        <div class="capability-examples">
          <strong>Try these:</strong>
          <ul>
            ${capability.examples.map(ex => `<li>"${ex}"</li>`).join('')}
          </ul>
        </div>
      ` : `
        <div class="capability-locked-info">
          <p class="setup-required">
            <strong>🔑 ${capability.setupInstructions}</strong>
          </p>
          <p class="unlock-hint">Once unlocked, you'll be able to:</p>
          <ul class="locked-examples">
            ${capability.examples.slice(0, 2).map(ex => `<li>${ex}</li>`).join('')}
          </ul>
          <button class="unlock-btn" onclick="showUnlockFlow('${capability.id}')">
            Unlock This Capability →
          </button>
        </div>
      `}
    `;

    capabilitiesGrid.appendChild(card);
  });
}

function showUnlockFlow(capabilityId) {
  const capability = CAPABILITIES.find(c => c.id === capabilityId);
  if (!capability) return;

  // Map capability requirements to settings sections
  const setupMap = {
    'gmail': 'settings-page',
    'calendar': 'settings-page',
    'slack': 'settings-page',
    'github': 'settings-page',
    'notion': 'settings-page',
    'cloud': 'settings-page'
  };

  // Show modal with instructions
  alert(`To unlock "${capability.title}":\n\n${capability.setupInstructions}\n\nHead to Settings to configure this integration.`);

  // Navigate to settings page
  const settingsLink = document.querySelector('[data-page="settings"]');
  if (settingsLink) {
    settingsLink.click();
  }
}

// Set up event listeners
document.addEventListener('DOMContentLoaded', () => {
  initializeProjectWorkspace();

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

  const analyzeStatusBtn = document.getElementById('analyze-status-btn');
  if (analyzeStatusBtn) {
    analyzeStatusBtn.addEventListener('click', analyzeProjectStatus);
  }

  // Initial status check
  checkServerStatus();
  refreshModelsList();
  checkChatConnection();
  checkGmailStatus();
  initAgentStatus();

  // Check connection status every 2 seconds
  connectionCheckInterval = setInterval(checkChatConnection, 2000);

  // Auto-load last model after letting servers fully start (3 seconds)
  // The function itself has additional waits and checks
  setTimeout(autoLoadLastModel, 3000);

  // Send proactive greeting after a short delay (let servers start)
  setTimeout(sendProactiveGreeting, 2000);
});

// Gmail Setup Functions
async function checkGmailStatus() {
  const statusText = document.getElementById('gmail-status-text');

  try {
    const response = await fetch('http://localhost:8001/credentials/gmail/status');
    const data = await response.json();

    if (data.configured) {
      statusText.textContent = 'Configured ✓';
      statusText.style.color = '#28a745';
    } else {
      statusText.textContent = 'Not configured';
      statusText.style.color = '#dc3545';
    }
  } catch (error) {
    statusText.textContent = 'Unable to check (MCP server offline)';
    statusText.style.color = '#6a737d';
  }
}

async function uploadGmailCredentials() {
  const fileInput = document.getElementById('gmail-credentials-file');
  const statusEl = document.getElementById('gmail-upload-status');
  const file = fileInput.files[0];

  if (!file) {
    statusEl.textContent = 'Please select a file';
    statusEl.style.color = '#dc3545';
    return;
  }

  try {
    statusEl.textContent = 'Uploading...';
    statusEl.style.color = '#0366d6';

    // Read file contents
    const fileContents = await file.text();

    // Validate it's JSON
    try {
      JSON.parse(fileContents);
    } catch (e) {
      throw new Error('Invalid JSON file');
    }

    // Upload to MCP server
    const response = await fetch('http://localhost:8001/credentials/upload', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        tool_name: 'gmail',
        credentials: fileContents
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Upload failed');
    }

    const result = await response.json();

    statusEl.textContent = result.message + ' ✓';
    statusEl.style.color = '#28a745';

    // Update status
    checkGmailStatus();

    // Clear file input
    fileInput.value = '';

  } catch (error) {
    statusEl.textContent = `Error: ${error.message}`;
    statusEl.style.color = '#dc3545';
  }
}

// Add event listener for Gmail upload
const uploadGmailBtn = document.getElementById('upload-gmail-credentials-btn');
if (uploadGmailBtn) {
  uploadGmailBtn.addEventListener('click', uploadGmailCredentials);
}

// API Keys Management
async function saveAPIKeys() {
  const anthropicKeyInput = document.getElementById('anthropic-api-key');
  const openaiKeyInput = document.getElementById('openai-api-key');
  const statusEl = document.getElementById('api-keys-status');

  const anthropicKey = anthropicKeyInput.value.trim();
  const openaiKey = openaiKeyInput.value.trim();

  if (!anthropicKey && !openaiKey) {
    statusEl.textContent = 'Please enter at least one API key';
    statusEl.style.color = '#dc3545';
    return;
  }

  // Save via Electron IPC
  if (typeof window.electron !== 'undefined') {
    try {
      statusEl.textContent = 'Saving API keys...';
      statusEl.style.color = '#0366d6';

      const { ipcRenderer } = window.electron;
      const config = {};

      if (anthropicKey) {
        config.anthropic_api_key = anthropicKey;
      }
      if (openaiKey) {
        config.openai_api_key = openaiKey;
      }

      const result = await ipcRenderer.invoke('update-config', config);

      if (result.success) {
        statusEl.textContent = 'API keys saved! Restart the server to use cloud models.';
        statusEl.style.color = '#28a745';

        // Clear the inputs (they're in .env now)
        anthropicKeyInput.value = '';
        openaiKeyInput.value = '';
      } else {
        statusEl.textContent = `Failed: ${result.error}`;
        statusEl.style.color = '#dc3545';
      }
    } catch (error) {
      statusEl.textContent = `Error: ${error.message}`;
      statusEl.style.color = '#dc3545';
    }
  } else {
    statusEl.textContent = 'API keys can only be saved in Electron app';
    statusEl.style.color = '#dc3545';
  }
}

// Load API key status (not the keys themselves - security)
async function loadAPIKeyStatus() {
  if (typeof window.electron !== 'undefined') {
    try {
      const { ipcRenderer } = window.electron;
      const config = await ipcRenderer.invoke('get-config');

      const anthropicKeyInput = document.getElementById('anthropic-api-key');
      const openaiKeyInput = document.getElementById('openai-api-key');

      // Show placeholder if key exists (don't show actual key for security)
      if (config.anthropic_api_key) {
        anthropicKeyInput.placeholder = '••••••••••••••••••••••• (configured)';
      }
      if (config.openai_api_key) {
        openaiKeyInput.placeholder = '••••••••••••••••••••••• (configured)';
      }
    } catch (error) {
      console.error('Failed to load API key status:', error);
    }
  }
}

// Add event listener for API keys save
const saveAPIKeysBtn = document.getElementById('save-api-keys-btn');
if (saveAPIKeysBtn) {
  saveAPIKeysBtn.addEventListener('click', saveAPIKeys);
}

// Load API key status when settings page loads
document.querySelectorAll('.sidebar a').forEach(link => {
  link.addEventListener('click', (e) => {
    const page = e.target.dataset.page;
    if (page === 'settings') {
      setTimeout(() => loadAPIKeyStatus(), 100);
    }
  });
});

// Drakyn Status Management
let agentStatusData = {
  state: 'idle', // idle, active, sleeping
  nextCheckTime: null,
  checkInterval: 30 * 60 * 1000 // 30 minutes in ms
};

function initAgentStatus() {
  // Listen for agent status updates from monitor service (via IPC)
  if (typeof window.electronAPI !== 'undefined') {
    window.electronAPI.receive('agent-status-update', (data) => {
      updateAgentStatus(data);
    });
  }

  // Start countdown timer
  updateAgentStatusDisplay();
  setInterval(updateAgentStatusDisplay, 1000); // Update every second
}

function updateAgentStatus(data) {
  agentStatusData = { ...agentStatusData, ...data };
  updateAgentStatusDisplay();
}

function updateAgentStatusDisplay() {
  const iconEl = document.getElementById('agent-status-icon');
  const textEl = document.getElementById('agent-status-text');
  const containerEl = document.querySelector('.agent-status');

  if (!iconEl || !textEl) return;

  // If next check time is set, calculate time remaining
  if (agentStatusData.nextCheckTime) {
    const now = Date.now();
    const timeRemaining = agentStatusData.nextCheckTime - now;

    if (timeRemaining > 0) {
      const minutes = Math.floor(timeRemaining / 60000);
      const seconds = Math.floor((timeRemaining % 60000) / 1000);

      if (minutes > 0) {
        iconEl.textContent = '😴';
        textEl.textContent = `Drakyn idle, waking up in ${minutes}m ${seconds}s`;
        containerEl.classList.remove('active');
      } else {
        iconEl.textContent = '⏰';
        textEl.textContent = `Drakyn resuming in ${seconds}s`;
        containerEl.classList.add('active');
      }
    } else {
      iconEl.textContent = '🤔';
      textEl.textContent = 'Drakyn checking context...';
      containerEl.classList.add('active');
    }
  } else {
    // No next check time set - agent is idle
    iconEl.textContent = '😴';
    textEl.textContent = 'Drakyn idle';
    containerEl.classList.remove('active');
  }

  // Override for active state
  if (agentStatusData.state === 'active') {
    iconEl.textContent = '🤔';
    textEl.textContent = 'Drakyn thinking...';
    containerEl.classList.add('active');
  } else if (agentStatusData.state === 'disabled') {
    iconEl.textContent = '💤';
    textEl.textContent = 'Drakyn monitoring disabled';
    containerEl.classList.remove('active');
  }
}

// Proactive Greeting on Startup
async function sendProactiveGreeting() {
  // Check if already greeted (session storage)
  if (sessionStorage.getItem('greeted')) return;

  // Wait for connection to be ready
  const connectionIndicator = document.getElementById('connection-indicator');
  if (!connectionIndicator || !connectionIndicator.classList.contains('connected')) {
    // Retry in 2 seconds
    setTimeout(sendProactiveGreeting, 2000);
    return;
  }

  try {
    // Read user context to personalize greeting
    const contextResponse = await fetch('http://localhost:8001/execute', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        tool: 'user_context',
        arguments: { action: 'read' }
      })
    });

    const contextData = await contextResponse.json();
    let userName = 'there';

    // Try to extract user name from context
    if (contextData.result && contextData.result.content) {
      const nameMatch = contextData.result.content.match(/Name:\s*(\w+)/i);
      if (nameMatch) {
        userName = nameMatch[1];
      }
    }

    // Get current time for time-appropriate greeting
    const hour = new Date().getHours();
    let timeGreeting = 'Hello';
    if (hour < 12) timeGreeting = 'Good morning';
    else if (hour < 18) timeGreeting = 'Good afternoon';
    else timeGreeting = 'Good evening';

    // Create greeting message
    const greeting = `${timeGreeting}, ${userName}! 👋\n\nI'm here and ready to help. I'm also monitoring in the background every 30 minutes to proactively suggest ways I can assist you.\n\nWhat would you like to work on today?`;

    // Add as agent message
    addMessage(greeting, false);
    updateProjectActivity(activeProjectId, 'Drakyn', greeting);

    // Set next check time (30 minutes from now)
    agentStatusData.nextCheckTime = Date.now() + agentStatusData.checkInterval;
    updateAgentStatusDisplay();

    // Mark as greeted
    sessionStorage.setItem('greeted', 'true');

  } catch (error) {
    console.error('Failed to send proactive greeting:', error);
    // Simple fallback greeting
    const fallback = 'Hello! I\'m here and ready to help. What can I do for you today?';
    addMessage(fallback, false);
    updateProjectActivity(activeProjectId, 'Drakyn', fallback);
    sessionStorage.setItem('greeted', 'true');
  }
}

// Auto-load last model on startup
async function autoLoadLastModel() {
  const lastModel = localStorage.getItem('lastModel');

  if (!lastModel) {
    console.log('No previous model found in localStorage');
    return;
  }

  console.log('Found last model in localStorage:', lastModel);

  // Wait longer for server to be ready (inference server can take time to start)
  await new Promise(resolve => setTimeout(resolve, 2000));

  // Check if server is responsive with a proper timeout using AbortController
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 3000);

    const healthCheck = await fetch(`${API_BASE_URL}/health`, {
      signal: controller.signal
    });
    clearTimeout(timeoutId);

    if (!healthCheck.ok) {
      console.log('Server not ready (not OK), skipping auto-load');
      return;
    }

    console.log('Server is ready, proceeding with auto-load');
  } catch (error) {
    console.log('Server not ready or timed out, skipping auto-load:', error.message);
    return;
  }

  // Load saved model settings
  const gpuMemory = parseFloat(localStorage.getItem('lastGpuMemory') || '0.9');
  const tensorParallel = parseInt(localStorage.getItem('lastTensorParallel') || '1');

  // Set form values
  const dropdown = document.getElementById('model-dropdown');
  const gpuMemoryInput = document.getElementById('gpu-memory');
  const tensorParallelInput = document.getElementById('tensor-parallel');

  if (dropdown) {
    dropdown.value = lastModel;
    // If not in dropdown, use text input
    if (!dropdown.value) {
      const modelPathInput = document.getElementById('model-path');
      if (modelPathInput) {
        modelPathInput.value = lastModel;
      }
    }
  }
  
  if (gpuMemoryInput) gpuMemoryInput.value = gpuMemory;
  if (tensorParallelInput) tensorParallelInput.value = tensorParallel;

  // Load the model
  const statusEl = document.getElementById('load-status');
  console.log('Attempting to auto-load model:', lastModel, 'with settings:', {
    gpuMemory,
    tensorParallel
  });

  if (statusEl) {
    statusEl.textContent = 'Auto-loading last model...';
    statusEl.style.color = '#dcdcaa';
  }

  try {
    const response = await fetch(`${API_BASE_URL}/load_model`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model_name_or_path: lastModel,
        gpu_memory_utilization: gpuMemory,
        tensor_parallel_size: tensorParallel
      })
    });

    const data = await response.json();
    console.log('Auto-load response:', data);

    if (response.ok) {
      if (statusEl) {
        statusEl.textContent = `Auto-loaded: ${lastModel}`;
        statusEl.style.color = '#4ec9b0';
      }
      console.log('✅ Successfully auto-loaded model:', lastModel);

      // Update UI
      refreshModelsList();
      checkServerStatus();
    } else {
      if (statusEl) {
        statusEl.textContent = `Failed to auto-load: ${data.detail}`;
        statusEl.style.color = '#f48771';
      }
      console.error('❌ Failed to auto-load model:', data.detail);
    }
  } catch (error) {
    if (statusEl) {
      statusEl.textContent = 'Auto-load failed - server may still be starting';
      statusEl.style.color = '#f48771';
    }
    console.error('❌ Auto-load error:', error.message);
  }
}
