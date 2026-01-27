// Notifications Management with WebSocket Integration
let notificationsList = [];
let unreadCount = 0;
let notificationsInitialized = false;

document.addEventListener('DOMContentLoaded', function() {
    const token = localStorage.getItem('auth_token');
    if (!token) {
        return;
    }
    
    initializeNotifications();
});

function initializeNotifications() {
    if (notificationsInitialized) return;
    
    // Load initial unread count
    loadUnreadCount();
    
    // Setup dropdown event listeners
    setupNotificationsDropdown();
    
    // Listen for WebSocket notifications (if chat.js is loaded)
    if (window.chatWebSocket) {
        setupWebSocketNotifications();
    } else {
        // Wait for WebSocket to be initialized
        const checkWebSocket = setInterval(() => {
            if (window.chatWebSocket) {
                setupWebSocketNotifications();
                clearInterval(checkWebSocket);
            }
        }, 100);
    }
    
    notificationsInitialized = true;
}

function setupNotificationsDropdown() {
    const dropdown = document.getElementById('notificationsDropdown');
    const notificationsListEl = document.getElementById('notifications-list');
    
    if (!dropdown) return;
    
    // Load notifications when dropdown is opened
    dropdown.addEventListener('show.bs.dropdown', function() {
        loadNotifications();
    });
    
    // Mark all as read button
    const markAllReadBtn = document.getElementById('mark-all-read-btn');
    if (markAllReadBtn) {
        markAllReadBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            markAllNotificationsRead();
        });
    }
    
    // View all notifications
    const viewAllBtn = document.getElementById('view-all-notifications');
    if (viewAllBtn) {
        viewAllBtn.addEventListener('click', function(e) {
            e.preventDefault();
            // Could navigate to a notifications page or scroll to chat
            if (typeof selectChatSection === 'function') {
                selectChatSection();
            }
        });
    }
}

function setupWebSocketNotifications() {
    // Override or extend the WebSocket message handler
    if (window.handleWebSocketMessage) {
        const originalHandler = window.handleWebSocketMessage;
        window.handleWebSocketMessage = function(data) {
            originalHandler(data);
            handleNotificationWebSocket(data);
        };
    } else {
        // If chat.js isn't loaded, create our own handler
        window.handleNotificationWebSocket = handleNotificationWebSocket;
    }
}

function handleNotificationWebSocket(data) {
    if (data.type === 'notification') {
        const notificationData = data.data;
        addNotificationToList(notificationData);
        updateUnreadCount();
        
        // Show browser notification if page is not focused
        if (document.hidden && 'Notification' in window && Notification.permission === 'granted') {
            showBrowserNotification(notificationData);
        }
    }
}

async function loadNotifications() {
    const notificationsListEl = document.getElementById('notifications-list');
    if (!notificationsListEl) return;
    
    notificationsListEl.innerHTML = `
        <div class="notification-loading text-center p-3">
            <div class="spinner-border spinner-border-sm" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <span class="ms-2">Loading notifications...</span>
        </div>
    `;
    
    try {
        const token = localStorage.getItem('auth_token');
        const response = await fetch('/api/v1/chat/notifications?limit=10&unread_only=false', {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            notificationsList = await response.json();
            renderNotifications();
        } else {
            notificationsListEl.innerHTML = `
                <div class="notification-empty text-center p-3">
                    <p class="text-muted mb-0">Failed to load notifications</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error loading notifications:', error);
        notificationsListEl.innerHTML = `
            <div class="notification-empty text-center p-3">
                <p class="text-muted mb-0">Error loading notifications</p>
            </div>
        `;
    }
}

function renderNotifications() {
    const notificationsListEl = document.getElementById('notifications-list');
    if (!notificationsListEl) return;
    
    if (!notificationsList || notificationsList.length === 0) {
        notificationsListEl.innerHTML = `
            <div class="notification-empty text-center p-3">
                <i class="bi bi-bell-slash" style="font-size: 2rem; color: #ccc;"></i>
                <p class="text-muted mb-0 mt-2">No notifications</p>
            </div>
        `;
        return;
    }
    
    notificationsListEl.innerHTML = notificationsList.map(notif => `
        <li class="notification-item ${notif.is_read ? '' : 'unread'}" 
            data-notification-id="${notif.id}"
            data-sender-id="${notif.sender_id || ''}"
            onclick="handleNotificationClick(${notif.id}, ${notif.related_chat_id || 'null'}, ${notif.sender_id || 'null'})">
            <div class="notification-content">
                <div class="notification-header">
                    <strong class="notification-title">${escapeHtml(notif.title)}</strong>
                    ${!notif.is_read ? '<span class="notification-dot"></span>' : ''}
                </div>
                <p class="notification-message">${escapeHtml(notif.message)}</p>
                <small class="notification-time">${formatNotificationTime(notif.created_at)}</small>
            </div>
        </li>
    `).join('');
}

function addNotificationToList(notificationData) {
    // Add to beginning of list
    notificationsList.unshift({
        id: notificationData.chat_id || Date.now(),
        title: notificationData.type === 'chat_message' ? 'New Message' : 'Notification',
        message: notificationData.message || '',
        notification_type: notificationData.type || 'info',
        is_read: false,
        related_chat_id: notificationData.chat_id,
        sender_id: notificationData.sender_id,
        created_at: notificationData.created_at || new Date().toISOString()
    });
    
    // Keep only last 10
    if (notificationsList.length > 10) {
        notificationsList = notificationsList.slice(0, 10);
    }
    
    // Update UI if dropdown is open
    const dropdown = document.getElementById('notificationsDropdown');
    if (dropdown && dropdown.classList.contains('show')) {
        renderNotifications();
    }
    
    updateUnreadCount();
}

async function loadUnreadCount() {
    try {
        const token = localStorage.getItem('auth_token');
        const response = await fetch('/api/v1/chat/notifications/unread-count', {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            unreadCount = data.unread_count || 0;
            updateNotificationBadge();
        }
    } catch (error) {
        console.error('Error loading unread count:', error);
    }
}

function updateUnreadCount() {
    unreadCount = notificationsList.filter(n => !n.is_read).length;
    updateNotificationBadge();
}

function updateNotificationBadge() {
    const badge = document.getElementById('notification-badge');
    if (!badge) return;
    
    if (unreadCount > 0) {
        badge.textContent = unreadCount > 99 ? '99+' : unreadCount;
        badge.style.display = 'inline-block';
    } else {
        badge.style.display = 'none';
    }
}

async function handleNotificationClick(notificationId, chatId, senderId) {
    // Mark notification as read
    await markNotificationRead(notificationId);
    
    // If it's a chat notification, open chat with the sender
    if (senderId && typeof selectChatUser === 'function') {
        selectChatSection();
        // Small delay to ensure chat section is loaded
        setTimeout(() => {
            if (typeof selectChatUser === 'function') {
                selectChatUser(senderId);
            }
        }, 300);
    } else if (chatId) {
        // Just switch to chat section
        selectChatSection();
    }
    
    // Close dropdown
    const dropdown = bootstrap.Dropdown.getInstance(document.getElementById('notificationsDropdown'));
    if (dropdown) {
        dropdown.hide();
    }
}

async function markNotificationRead(notificationId) {
    try {
        const token = localStorage.getItem('auth_token');
        const response = await fetch(`/api/v1/chat/notifications/${notificationId}/read`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            // Update local list
            const notif = notificationsList.find(n => n.id === notificationId);
            if (notif) {
                notif.is_read = true;
            }
            
            // Update UI
            const notifItem = document.querySelector(`[data-notification-id="${notificationId}"]`);
            if (notifItem) {
                notifItem.classList.remove('unread');
                const dot = notifItem.querySelector('.notification-dot');
                if (dot) dot.remove();
            }
            
            updateUnreadCount();
        }
    } catch (error) {
        console.error('Error marking notification as read:', error);
    }
}

async function markAllNotificationsRead() {
    try {
        const token = localStorage.getItem('auth_token');
        const response = await fetch('/api/v1/chat/notifications/read-all', {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            // Update local list
            notificationsList.forEach(notif => {
                notif.is_read = true;
            });
            
            // Update UI
            renderNotifications();
            updateUnreadCount();
        }
    } catch (error) {
        console.error('Error marking all notifications as read:', error);
    }
}

function formatNotificationTime(dateString) {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    
    return date.toLocaleDateString();
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showBrowserNotification(notificationData) {
    new Notification(notificationData.title || 'New Notification', {
        body: notificationData.message || '',
        icon: '/static/images/notification-icon.png',
        tag: 'notification-' + notificationData.chat_id
    });
}

function selectChatSection() {
    const chatNavItem = document.querySelector('[data-section="chat"]');
    if (chatNavItem) {
        chatNavItem.click();
    }
}

// Request notification permission on page load
if ('Notification' in window && Notification.permission === 'default') {
    Notification.requestPermission();
}

// Make functions globally available
window.handleNotificationClick = handleNotificationClick;
window.selectChatSection = selectChatSection;

