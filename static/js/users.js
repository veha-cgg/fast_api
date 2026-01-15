// Helper functions
function getAuthHeaders() {
    const token = localStorage.getItem('auth_token');
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    };
}

function handleApiError(response) {
    if (response.status === 401) {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user_data');
        window.location.href = '/login';
        return true;
    }
    return false;
}

// Load users data
async function loadUsers() {
    const tbody = document.getElementById('users-table-body');
    if (!tbody) {
        console.error('Users table body not found');
        return;
    }
    
    tbody.innerHTML = '<tr><td colspan="6" class="text-center">Loading...</td></tr>';

    try {
        const token = localStorage.getItem('auth_token');
        if (!token) {
            window.location.href = '/login';
            return;
        }
        
        const response = await fetch('/api/v1/users/get-users', {
            headers: getAuthHeaders()
        });
        
        if (handleApiError(response)) return;
        
        if (response.ok) {
            const users = await response.json();
            const totalUsers = users.length || 0;
            
            // Update total users count in users section
            const totalUsersEl = document.getElementById('total-users');
            if (totalUsersEl && totalUsersEl.classList.contains('total-users-count')) {
                totalUsersEl.textContent = `Total Users: ${totalUsers}`;
            }
            
            if (users.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" class="text-center">No users found</td></tr>';
                return;
            }

            tbody.innerHTML = users.map(user => `
                <tr>
                    <td>${user.id || 'N/A'}</td>
                    <td>${user.name || 'N/A'}</td>
                    <td>${user.email || 'N/A'}</td>
                    <td><span class="${user.role === 'admin' ? 'bg-role-admin' : 'bg-role-user'}">${user.role || 'user'}</span></td>
                    <td><span class="${user.is_active ? 'bg-status-active' : 'bg-status-inactive'}">${user.is_active ? '<i class="bi bi-check-circle"></i> Active' : '<i class="bi bi-x-circle"></i> Inactive'}</span></td>
                    <td>
                        <button class="btn btn-sm btn-action btn-edit" onclick="editUser(${user.id})">
                        <i class="bi bi-pencil"></i>
                        </button>
                        <button class="btn btn-sm btn-action btn-view" onclick="viewUser(${user.id})">
                        <i class="bi bi-eye"></i>
                        </button>
                        <button class="btn btn-sm btn-action btn-delete" onclick="deleteUser(${user.id})">
                        <i class="bi bi-trash"></i>
                        </button>
                    </td>
                </tr>
            `).join('');
        } else {
            const errorData = await response.json().catch(() => ({}));
            const errorMsg = errorData.detail || 'Error loading users';
            tbody.innerHTML = `<tr><td colspan="6" class="text-center text-danger">${errorMsg}</td></tr>`;
        }
    } catch (error) {
        console.error('Error loading users:', error);
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-danger">Error loading users</td></tr>';
    }
}

// Get total users count
async function getTotalUsers() {
    try {
        const token = localStorage.getItem('auth_token');
        if (!token) {
            return 0;
        }
        
        const response = await fetch('/api/v1/users/get-users', {
            headers: getAuthHeaders()
        });
        
        if (handleApiError(response)) return 0;
        
        if (response.ok) {
            const users = await response.json();
            return users.length || 0;
        } else {
            console.error('Failed to load users:', response.status);
            return 0;
        }
    } catch (error) {
        console.error('Error loading total users:', error);
        return 0;
    }
}

// Load total users count to dashboard
async function loadTotalUsers() {
    const totalUsersEl = document.getElementById('total-users');
    if (totalUsersEl) {
        const totalUsers = await getTotalUsers();
        totalUsersEl.textContent = totalUsers;
    }
}

// Modern Toast Notification System
function showToast(message, type = 'info', duration = 3000) {
    // Remove existing toast container if any
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container';
        document.body.appendChild(toastContainer);
    }

    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    // Icons based on type
    const icons = {
        success: '<i class="bi bi-check-circle-fill"></i>',
        error: '<i class="bi bi-x-circle-fill"></i>',
        warning: '<i class="bi bi-exclamation-triangle-fill"></i>',
        info: '<i class="bi bi-info-circle-fill"></i>'
    };

    toast.innerHTML = `
        <div class="toast-content">
            <div class="toast-icon">${icons[type] || icons.info}</div>
            <div class="toast-message">${message}</div>
            <button class="toast-close" onclick="this.parentElement.parentElement.remove()">
                <i class="bi bi-x"></i>
            </button>
        </div>
        <div class="toast-progress"></div>
    `;

    toastContainer.appendChild(toast);

    // Trigger animation
    setTimeout(() => {
        toast.classList.add('show');
    }, 10);

    // Auto remove
    const progressBar = toast.querySelector('.toast-progress');
    progressBar.style.animation = `toastProgress ${duration}ms linear forwards`;

    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => {
            toast.remove();
            if (toastContainer.children.length === 0) {
                toastContainer.remove();
            }
        }, 300);
    }, duration);
}

// Sidebar Toggle Function
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar-col');
    const toggleIcon = document.getElementById('sidebarToggleIcon');
    
    if (sidebar) {
        sidebar.classList.toggle('collapsed');
        if (sidebar.classList.contains('collapsed')) {
            toggleIcon.classList.remove('bi-chevron-left');
            toggleIcon.classList.add('bi-chevron-right');
        } else {
            toggleIcon.classList.remove('bi-chevron-right');
            toggleIcon.classList.add('bi-chevron-left');
        }
    }
}

// User Page Management
let currentUserPageMode = null;

function openUserPage(mode, userId = null) {
    console.log('openUserPage called with mode:', mode, 'userId:', userId);
    currentUserPageMode = mode;
    const overlay = document.getElementById('userPageOverlay');
    const form = document.getElementById('userForm');
    const submitBtn = document.getElementById('userPageSubmitBtn');
    const passwordGroup = document.getElementById('password-group');
    const iconEl = document.getElementById('userPageIcon');
    const titleEl = document.getElementById('userPageTitle');
    const subtitleEl = document.getElementById('userPageSubtitle');
    
    if (!overlay) {
        console.error('User page overlay not found');
        showToast('User page overlay not found. Please refresh the page.', 'error', 3000);
        return;
    }
    
    if (!form) {
        console.error('User form not found');
        showToast('User form not found. Please refresh the page.', 'error', 3000);
        return;
    }
    
    // Reset form
    if (form) {
        form.reset();
    }
    const userIdInput = document.getElementById('user-id');
    if (userIdInput) {
        userIdInput.value = '';
    }
    
    // Set mode-specific content
    if (mode === 'view') {
        titleEl.textContent = 'View User';
        subtitleEl.textContent = 'User information (read-only)';
        iconEl.innerHTML = '<i class="bi bi-eye-fill"></i>';
        submitBtn.style.display = 'none';
        passwordGroup.style.display = 'none';
        form.querySelectorAll('input, select').forEach(input => {
            input.setAttribute('readonly', 'readonly');
            input.setAttribute('disabled', 'disabled');
        });
        loadUserData(userId);
    } else if (mode === 'edit') {
        titleEl.textContent = 'Edit User';
        subtitleEl.textContent = 'Update user information';
        iconEl.innerHTML = '<i class="bi bi-pencil-fill"></i>';
        submitBtn.innerHTML = '<i class="bi bi-check"></i> Update';
        submitBtn.style.display = 'flex';
        passwordGroup.style.display = 'block';
        passwordGroup.querySelector('input').removeAttribute('required');
        form.querySelectorAll('input, select').forEach(input => {
            input.removeAttribute('readonly');
            input.removeAttribute('disabled');
        });
        loadUserData(userId);
    } else if (mode === 'add') {
        titleEl.textContent = 'Add New User';
        subtitleEl.textContent = 'Create a new user account';
        iconEl.innerHTML = '<i class="bi bi-person-plus-fill"></i>';
        submitBtn.innerHTML = '<i class="bi bi-check"></i> Create';
        submitBtn.style.display = 'flex';
        passwordGroup.style.display = 'block';
        passwordGroup.querySelector('input').setAttribute('required', 'required');
        form.querySelectorAll('input, select').forEach(input => {
            input.removeAttribute('readonly');
            input.removeAttribute('disabled');
        });
    }
    
    overlay.classList.add('show');
    document.body.style.overflow = 'hidden';
}

function closeUserPage() {
    const overlay = document.getElementById('userPageOverlay');
    if (overlay) {
        overlay.classList.remove('show');
        document.body.style.overflow = '';
        currentUserPageMode = null;
    }
}

async function loadUserData(userId) {
    try {
        const response = await fetch(`/api/v1/users/get-user/${userId}`, {
            headers: getAuthHeaders()
        });
        
        if (handleApiError(response)) {
            closeUserPage();
            return;
        }
        
        if (response.ok) {
            const user = await response.json();
            document.getElementById('user-id').value = user.id || '';
            document.getElementById('user-name').value = user.name || '';
            document.getElementById('user-email').value = user.email || '';
            document.getElementById('user-role').value = user.role || 'user';
            document.getElementById('user-status').value = user.is_active ? 'true' : 'false';
        } else {
            const errorData = await response.json().catch(() => ({}));
            showToast(errorData.detail || 'Failed to load user data', 'error', 3000);
        }
    } catch (error) {
        console.error('Error loading user data:', error);
        showToast('Error loading user data. Please try again.', 'error', 3000);
    }
}

// Action functions
function viewUser(userId) {
    openUserPage('view', userId);
}

function editUser(userId) {
    openUserPage('edit', userId);
}

function addUser() {
    console.log('addUser called');
    openUserPage('add');
}

// Handle form submission
document.addEventListener('DOMContentLoaded', function() {
    const userForm = document.getElementById('userForm');
    if (userForm) {
        userForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(userForm);
            const userId = formData.get('user_id');
            const userData = {
                name: formData.get('name'),
                email: formData.get('email'),
                role: formData.get('role'),
                is_active: formData.get('is_active') === 'true'
            };
            
            const password = formData.get('password');
            if (password) {
                userData.password = password;
            }
            
            try {
                let response;
                if (userId && currentUserPageMode === 'edit') {
                    response = await fetch(`/api/v1/users/update-user/${userId}`, {
                        method: 'PUT',
                        headers: getAuthHeaders(),
                        body: JSON.stringify(userData)
                    });
                } else {
                    if (!password) {
                        showToast('Password is required for new users', 'error', 3000);
                        return;
                    }
                    response = await fetch('/api/v1/users/create-user', {
                        method: 'POST',
                        headers: getAuthHeaders(),
                        body: JSON.stringify(userData)
                    });
                }
                
                if (handleApiError(response)) return;
                
                if (response.ok) {
                    const action = userId ? 'updated' : 'created';
                    showToast(`User ${action} successfully`, 'success', 3000);
                    closeUserPage();
                    setTimeout(() => loadUsers(), 500);
                } else {
                    const errorData = await response.json().catch(() => ({}));
                    showToast(errorData.detail || 'Failed to save user', 'error', 3000);
                }
            } catch (error) {
                console.error('Error saving user:', error);
                showToast('Error saving user. Please try again.', 'error', 3000);
            }
        });
    }
    
    // Close user page on Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            const overlay = document.getElementById('userPageOverlay');
            if (overlay && overlay.classList.contains('show')) {
                closeUserPage();
            }
        }
    });
});

let currentDeleteUserId = null;

function deleteUser(userId) {
    currentDeleteUserId = userId;
    const modal = document.getElementById('deleteUserModal');
    const userIdSpan = document.getElementById('modal-user-id');
    
    if (userIdSpan) {
        userIdSpan.textContent = userId;
    }
    
    if (modal) {
        modal.classList.add('show');
        document.body.style.overflow = 'hidden';
        
        // Set up confirm button
        const confirmBtn = document.getElementById('confirmDeleteBtn');
        if (confirmBtn) {
            // Remove old event listeners
            const newConfirmBtn = confirmBtn.cloneNode(true);
            confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);
            newConfirmBtn.addEventListener('click', () => confirmDeleteUser(userId));
        }
    }
}

function closeDeleteModal() {
    const modal = document.getElementById('deleteUserModal');
    if (modal) {
        modal.classList.remove('show');
        document.body.style.overflow = '';
        currentDeleteUserId = null;
    }
}

async function confirmDeleteUser(userId) {
    try {
        const response = await fetch(`/api/v1/users/delete-user/${userId}`, {
            method: 'DELETE',
            headers: getAuthHeaders()
        });

        if (handleApiError(response)) {
            closeDeleteModal();
            return;
        }

        if (response.ok) {
            closeDeleteModal();
            showToast(`User ID: ${userId} deleted successfully`, 'success', 3000);
            // Reload users list
            setTimeout(() => loadUsers(), 500);
        } else {
            const errorData = await response.json().catch(() => ({}));
            showToast(errorData.detail || 'Failed to delete user', 'error', 3000);
        }
    } catch (error) {
        console.error('Error deleting user:', error);
        showToast('Error deleting user. Please try again.', 'error', 3000);
    }
}

// Close modal when clicking outside
document.addEventListener('click', function(event) {
    const modal = document.getElementById('deleteUserModal');
    if (modal && event.target === modal) {
        closeDeleteModal();
    }
});

// Close modal on Escape key
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closeDeleteModal();
    }
});

// Export users
function exportUsers() {
    showToast('Exporting users data...', 'info', 2000);
    // TODO: Implement export functionality
    setTimeout(() => {
        showToast('Users data exported successfully', 'success', 3000);
    }, 2000);
}

