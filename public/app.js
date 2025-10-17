// Simple page navigation
document.querySelectorAll('.sidebar a').forEach(link => {
  link.addEventListener('click', (e) => {
    e.preventDefault();
    const page = e.target.dataset.page;

    // Hide all pages
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));

    // Show selected page
    document.getElementById(`${page}-page`).classList.add('active');
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

function sendMessage() {
  const message = messageInput.value.trim();
  if (message) {
    addMessage(message, true);
    messageInput.value = '';

    // TODO: Send to backend and get response
    setTimeout(() => {
      addMessage('Backend not yet connected. Coming soon!', false);
    }, 500);
  }
}

sendButton.addEventListener('click', sendMessage);
messageInput.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') {
    sendMessage();
  }
});
