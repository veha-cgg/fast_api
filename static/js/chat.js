// Chat WebSocket and UI Management
let chatWebSocket = null;
let currentUserId = null;
let currentChatUserId = null;
let usersList = [];
let messagesCache = {};

window.chatInitialized = false;

document.addEventListener('DOMContentLoaded', function() {
    const token = localStorage.getItem('auth_token');
    if (!token) {
        window.location.href = '/login';
        return;
    }

    initializeChat();
});

function initializeChat() {
    if (window.chatInitialized) {
        return; // Already initialized
    }
    
    const userData = JSON.parse(localStorage.getItem('user_data') || '{}');
    currentUserId = userData.id;
    
    if (!currentUserId) {
        console.error('User ID not found');
        return;
    }
    connectWebSocket();
    loadChatUsers();
    setupChatEventListeners();
    setupUserSearch();
    
    window.chatInitialized = true;
}

function connectWebSocket() {
    const token = localStorage.getItem('auth_token');
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/chat?token=${token}`;
    
    chatWebSocket = new WebSocket(wsUrl);
    window.chatWebSocket = chatWebSocket;
    
    chatWebSocket.onopen = function() {
        console.log('WebSocket connected');
        updateCurrentUserStatus(true);
        if (window.chatPingInterval) {
            clearInterval(window.chatPingInterval);
        }
        window.chatPingInterval = setInterval(() => {
            if (chatWebSocket && chatWebSocket.readyState === WebSocket.OPEN) {
                chatWebSocket.send(JSON.stringify({ type: 'ping' }));
            }
        }, 30000);
    };
    
    chatWebSocket.onmessage = function(event) {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
    };
    
    chatWebSocket.onerror = function(error) {
        console.error('WebSocket error:', error);
    };
    
    chatWebSocket.onclose = function() {
        console.log('WebSocket disconnected');
        updateCurrentUserStatus(false);
        if (window.chatPingInterval) {
            clearInterval(window.chatPingInterval);
        }
        setTimeout(connectWebSocket, 3000);
    };
}

function handleWebSocketMessage(data) {
    switch(data.type) {
        case 'connected':
            console.log('Connected to chat:', data.message);
            break;
            
        case 'notification':
            handleNewMessage(data.data);
            // Also handle notification for notifications dropdown
            if (window.handleNotificationWebSocket) {
                window.handleNotificationWebSocket(data);
            }
            break;
            
        case 'message_sent':
            break;
            
        case 'user_status_update':
            updateUserOnlineStatus(data.user_id, data.is_online);
            break;
            
        case 'error':
            console.error('Chat error:', data.message);
            showNotification(data.message, 'error');
            break;
            
        case 'pong':
            break;
    }
}

// Make WebSocket globally available for notifications.js
window.chatWebSocket = chatWebSocket;
window.handleWebSocketMessage = handleWebSocketMessage;

function handleNewMessage(messageData) {
    if (currentChatUserId && 
        (messageData.sender_id === currentChatUserId || 
         (messageData.receiver_id === currentUserId && messageData.sender_id === currentChatUserId))) {
        addMessageToChat(messageData);
    }
    updateUserUnreadStatus(messageData.sender_id);
    playNotificationSound();
}

function setupChatEventListeners() {
    const sendBtn = document.getElementById('send-message-btn');
    const messageInput = document.getElementById('chat-message-input');
    
    if (sendBtn) {
        sendBtn.addEventListener('click', sendMessage);
    }
    
    if (messageInput) {
        messageInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }
}

function setupUserSearch() {
    const searchInput = document.getElementById('user-search');
    if (searchInput) {
        searchInput.addEventListener('input', function(e) {
            filterUsers(e.target.value);
        });
    }
}

async function loadChatUsers() {
    try {
        const token = localStorage.getItem('auth_token');
        const response = await fetch('/api/v1/users/chat-users', {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            usersList = await response.json();
            renderUsersList(usersList);
            
            loadOnlineUsers();
        } else {
            console.error('Failed to load users');
            document.getElementById('chat-users-list').innerHTML = 
                '<div class="loading-users"><span>Failed to load users</span></div>';
        }
    } catch (error) {
        console.error('Error loading users:', error);
    }
}

async function loadOnlineUsers() {
    try {
        const token = localStorage.getItem('auth_token');
        const response = await fetch('/api/v1/chat/users/online', {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            const onlineUsers = await response.json();
            const onlineUserIds = new Set(onlineUsers.map(u => u.id));
            
            usersList.forEach(user => {
                user.is_online = onlineUserIds.has(user.id);
            });
            
            renderUsersList(usersList);
        }
    } catch (error) {
        console.error('Error loading online users:', error);
    }
}

function renderUsersList(users) {
    const usersListContainer = document.getElementById('chat-users-list');
    
    if (!users || users.length === 0) {
        usersListContainer.innerHTML = 
            '<div class="loading-users"><span>No users available</span></div>';
        return;
    }
    
    usersListContainer.innerHTML = users.map(user => `
        <div class="chat-user-item" data-user-id="${user.id}" onclick="selectChatUser(${user.id})">
            <div class="user-avatar">
                ${getUserInitials(user.name)}
            </div>
            <div class="user-info">
                <div class="user-name">${escapeHtml(user.name)}</div>
                <div class="user-status-text">
                    <span class="status-dot ${user.is_online ? 'online' : 'offline'}"></span>
                    <span>${user.is_online ? 'Online' : 'Offline'}</span>
                </div>
            </div>
        </div>
    `).join('');
}

function filterUsers(searchTerm) {
    const filtered = usersList.filter(user => 
        user.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        user.email.toLowerCase().includes(searchTerm.toLowerCase())
    );
    renderUsersList(filtered);
}

function selectChatUser(userId) {
    currentChatUserId = userId;
    
    document.querySelectorAll('.chat-user-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelector(`[data-user-id="${userId}"]`).classList.add('active');
    
    document.getElementById('no-chat-selected').style.display = 'none';
    document.getElementById('chat-window').style.display = 'flex';
    
    const user = usersList.find(u => u.id === userId);
    if (user) {
        document.getElementById('chat-user-name').textContent = user.name;
        document.getElementById('chat-user-initial').textContent = getUserInitials(user.name);
        
        const statusElement = document.getElementById('chat-user-status');
        statusElement.innerHTML = `
            <span class="status-dot ${user.is_online ? 'online' : 'offline'}"></span>
            <span>${user.is_online ? 'Online' : 'Offline'}</span>
        `;
    }
    
    loadChatMessages(userId);
}

async function loadChatMessages(receiverId) {
    const messagesContainer = document.getElementById('chat-messages');
    messagesContainer.innerHTML = '<div class="loading-users"><div class="spinner-border spinner-border-sm"></div><span>Loading messages...</span></div>';
    
    try {
        const token = localStorage.getItem('auth_token');
        const response = await fetch(
            `/api/v1/chat/messages?receiver_id=${receiverId}&limit=50`,
            {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            }
        );
        
        if (response.ok) {
            const messages = await response.json();
            messagesContainer.innerHTML = '';
            
            if (messages.length === 0) {
                messagesContainer.innerHTML = 
                    '<div class="no-chat-selected"><p>No messages yet. Start the conversation!</p></div>';
                return;
            }
            
            messages.forEach(message => {
                addMessageToChat(message);
            });
            scrollToBottom();
        } else {
            messagesContainer.innerHTML = '<div class="loading-users"><span>Failed to load messages</span></div>';
        }
    } catch (error) {
        console.error('Error loading messages:', error);
        messagesContainer.innerHTML = '<div class="loading-users"><span>Error loading messages</span></div>';
    }
}

function addMessageToChat(messageData) {
    const messagesContainer = document.getElementById('chat-messages');
    const isSent = messageData.sender_id === currentUserId;
    
    const messageElement = document.createElement('div');
    messageElement.className = `message ${isSent ? 'sent' : 'received'}`;
    
    const time = messageData.created_at ? 
        new Date(messageData.created_at).toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit' 
        }) : '';
    
    messageElement.innerHTML = `
        <div class="message-content">
            <p class="message-text">${escapeHtml(messageData.message)}</p>
            <div class="message-time">${time}</div>
        </div>
    `;
    
    messagesContainer.appendChild(messageElement);
    scrollToBottom();
}

function sendMessage() {
    const messageInput = document.getElementById('chat-message-input');
    const message = messageInput.value.trim();
    
    if (!message || !currentChatUserId || !chatWebSocket || chatWebSocket.readyState !== WebSocket.OPEN) {
        return;
    }
    
    const messageData = {
        type: 'chat_message',
        receiver_id: currentChatUserId,
        message: message
    };
    
    chatWebSocket.send(JSON.stringify(messageData));
    
    messageInput.value = '';
    
    const tempMessage = {
        id: Date.now(),
        message: message,
        sender_id: currentUserId,
        receiver_id: currentChatUserId,
        created_at: new Date().toISOString()
    };
    addMessageToChat(tempMessage);
}

function scrollToBottom() {
    const messagesContainer = document.getElementById('chat-messages');
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function getUserInitials(name) {
    if (!name) return 'U';
    const parts = name.trim().split(' ');
    if (parts.length >= 2) {
        return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    }
    return name[0].toUpperCase();
}

function updateCurrentUserStatus(isOnline) {
    const statusElement = document.getElementById('current-user-name');
    if (statusElement) {
        const userData = JSON.parse(localStorage.getItem('user_data') || '{}');
        statusElement.textContent = userData.name || 'You';
    }
}

function updateUserOnlineStatus(userId, isOnline) {
    const user = usersList.find(u => u.id === userId);
    if (user) {
        user.is_online = isOnline;
        
        const userItem = document.querySelector(`[data-user-id="${userId}"]`);
        if (userItem) {
            const statusDot = userItem.querySelector('.status-dot');
            const statusText = userItem.querySelector('.user-status-text span:last-child');
            
            if (statusDot) {
                statusDot.className = `status-dot ${isOnline ? 'online' : 'offline'}`;
            }
            if (statusText) {
                statusText.textContent = isOnline ? 'Online' : 'Offline';
            }
        }
        
        if (userId === currentChatUserId) {
            const statusElement = document.getElementById('chat-user-status');
            if (statusElement) {
                statusElement.innerHTML = `
                    <span class="status-dot ${isOnline ? 'online' : 'offline'}"></span>
                    <span>${isOnline ? 'Online' : 'Offline'}</span>
                `;
            }
        }
    }
}

function updateUserUnreadStatus(userId) {
    const userItem = document.querySelector(`[data-user-id="${userId}"]`);
    if (userItem && userId !== currentChatUserId) {
        if (!userItem.querySelector('.unread-badge')) {
            const badge = document.createElement('span');
            badge.className = 'unread-badge';
            badge.style.cssText = 'background: var(--primary-color); color: white; border-radius: 50%; width: 8px; height: 8px; position: absolute; top: 1rem; right: 1rem;';
            userItem.style.position = 'relative';
            userItem.appendChild(badge);
        }
    }
}

function playNotificationSound() {
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showNotification(message, type = 'info') {
    console.log(`[${type.toUpperCase()}] ${message}`);
}

if (typeof loadSectionData === 'function') {
    const originalLoadSectionData = loadSectionData;
    loadSectionData = function(section) {
        if (section === 'chat') {
            return;
        }
        originalLoadSectionData(section);
    };
}

