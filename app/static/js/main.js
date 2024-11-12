// WebSocket connection
let ws;
let reconnectAttempts = 0;
const maxReconnectAttempts = 5;

function connectWebSocket() {
    ws = new WebSocket(`ws://${window.location.host}/ws`);

    ws.onmessage = function(event) {
        const data = JSON.parse(event.data);
        if (data.type === 'message') {
            appendMessage(`[${data.topic}] ${data.payload}`);
        } else if (data.type === 'status') {
            showStatus(data.message);
        }
    };

    ws.onclose = function() {
        if (reconnectAttempts < maxReconnectAttempts) {
            setTimeout(connectWebSocket, 1000);
            reconnectAttempts++;
        }
    };

    ws.onerror = function(error) {
        console.error('WebSocket error:', error);
        showStatus('WebSocket connection error', true);
    };
}

// Message handling
function appendMessage(message) {
    const messagesDiv = document.getElementById('messages');
    const messageElement = document.createElement('div');
    messageElement.className = 'message-item';
    messageElement.textContent = message;
    messagesDiv.appendChild(messageElement);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function clearMessages() {
    const messagesDiv = document.getElementById('messages');
    messagesDiv.innerHTML = '';
}

// Status message handling
function showStatus(message, isError = false) {
    const statusEl = document.getElementById('statusMessage');
    statusEl.textContent = message;
    statusEl.classList.remove('hidden');
    statusEl.classList.remove('bg-gray-800', 'bg-red-500');
    statusEl.classList.add(isError ? 'bg-red-500' : 'bg-gray-800');

    setTimeout(() => {
        statusEl.classList.add('hidden');
    }, 3000);
}

// MQTT operations
async function connect() {
    const host = document.getElementById('host').value;
    const port = document.getElementById('port').value;
    const username = document.getElementById('username')?.value;
    const password = document.getElementById('password')?.value;

    const formData = new FormData();
    formData.append('host', host);
    formData.append('port', port);
    if (username) formData.append('username', username);
    if (password) formData.append('password', password);

    try {
        const response = await fetch('/api/connect', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        showStatus(data.message, data.status !== 'success');

        if (data.status === 'success') {
            window.location.href = '/dashboard';
        }
    } catch (error) {
        showStatus('Connection failed', true);
    }
}

async function disconnect() {
    try {
        const response = await fetch('/api/disconnect', {
            method: 'POST'
        });

        const data = await response.json();
        showStatus(data.message, data.status !== 'success');

        if (data.status === 'success') {
            window.location.href = '/connect';
        }
    } catch (error) {
        showStatus('Disconnection failed', true);
    }
}

// Initialize WebSocket connection when page loads
document.addEventListener('DOMContentLoaded', function() {
    connectWebSocket();
});