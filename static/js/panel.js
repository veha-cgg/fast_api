
document.addEventListener('DOMContentLoaded', function() {
    const token = localStorage.getItem('auth_token');
    if (!token) {
        window.location.href = '/login';
        return;
    }
    
    initializePanel();
});

function initializePanel() {
    const navItems = document.querySelectorAll('.list-group-item[data-section]');
    const contentSections = document.querySelectorAll('.content-section');

    navItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            
            navItems.forEach(nav => nav.classList.remove('active'));
            
            this.classList.add('active');
            
            contentSections.forEach(section => {
                section.style.display = 'none';
            });
            
            const sectionId = this.getAttribute('data-section') + '-section';
            const targetSection = document.getElementById(sectionId);
            if (targetSection) {
                targetSection.style.display = 'block';
                
                loadSectionData(this.getAttribute('data-section'));
            }
        });
    });

    loadDashboardData();
    
    displayUserInfo();
}

function displayUserInfo() {
    const userData = JSON.parse(localStorage.getItem('user_data') || '{}');
    if (userData && (userData.name || userData.email)) {
        const userNameEl = document.getElementById('user-name');
        const userEmailEl = document.getElementById('user-email');
        if (userNameEl) {
            userNameEl.textContent = userData.name || userData.email || 'User';
        }
        if (userEmailEl) {
            userEmailEl.textContent = userData.email || userData.name || 'name@example.com';
        }
    }
}

function logout() {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_data');
    window.location.href = '/login';
}

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

async function loadDashboardData() {
    try {
        const token = localStorage.getItem('auth_token');
        if (!token) {
            window.location.href = '/login';
            return;
        }
        
        // Load total users from users.js
        if (typeof loadTotalUsers === 'function') {
            await loadTotalUsers();
        }
        
        const categoriesResponse = await fetch('/api/v1/categories/get-categories', {
            headers: getAuthHeaders()
        });
        
        if (handleApiError(categoriesResponse)) return;
        
        if (categoriesResponse.ok) {
            const categories = await categoriesResponse.json();
            document.getElementById('total-categories').textContent = categories.length || 0;
        } else {
            console.error('Failed to load categories:', categoriesResponse.status);
        }
        
        const imagesResponse = await fetch('/api/v1/images/get-images', {
            headers: getAuthHeaders()
        });
        
        if (handleApiError(imagesResponse)) return;
        
        if (imagesResponse.ok) {
            const images = await imagesResponse.json();
            document.getElementById('total-images').textContent = images.data.length || 0;
        } else {
            console.error('Failed to load images:', imagesResponse.status);
        }
    } catch (error) {
        console.error('Error loading dashboard data:', error);
    }
}

function loadSectionData(section) {
    switch(section) {
        case 'users':
            if (typeof loadUsers === 'function') {
                loadUsers();
            }
            break;
        case 'categories':
            loadCategories();
            break;
        case 'images':
            loadImages();
            break;
        case 'dashboard':
            loadDashboardData();
            break;
        case 'chat':
            // Initialize chat if not already initialized
            if (typeof initializeChat === 'function' && !window.chatInitialized) {
                initializeChat();
                window.chatInitialized = true;
            }
            break;
    }
}

async function loadCategories() {
    const tbody = document.getElementById('categories-table-body');
    tbody.innerHTML = '<tr><td colspan="4" class="text-center">Loading...</td></tr>';

    try {
        const token = localStorage.getItem('auth_token');
        if (!token) {
            window.location.href = '/login';
            return;
        }
        
        const response = await fetch('/api/v1/categories/get-categories', {
            headers: getAuthHeaders()
        });
        
        if (handleApiError(response)) return;
        
        if (response.ok) {
            const categories = await response.json();
            
            if (categories.length === 0) {
                tbody.innerHTML = '<tr><td colspan="4" class="text-center">No categories found</td></tr>';
                return;
            }

            tbody.innerHTML = categories.map(category => `
                <tr>
                    <td>${category.id || 'N/A'}</td>
                    <td>${category.name || 'N/A'}</td>
                    <td>${category.description || 'No description'}</td>
                    <td>
                        <button class="btn btn-sm btn-primary btn-action" onclick="viewCategory(${category.id})">View</button>
                        <button class="btn btn-sm btn-danger btn-action" onclick="deleteCategory(${category.id})">Delete</button>
                    </td>
                </tr>
            `).join('');
        } else {
            const errorData = await response.json().catch(() => ({}));
            const errorMsg = errorData.detail || 'Error loading categories';
            tbody.innerHTML = `<tr><td colspan="4" class="text-center text-danger">${errorMsg}</td></tr>`;
        }
    } catch (error) {
        console.error('Error loading categories:', error);
        tbody.innerHTML = '<tr><td colspan="4" class="text-center text-danger">Error loading categories</td></tr>';
    }
}

// Load images data
async function loadImages() {
    const tbody = document.getElementById('images-table-body');
    tbody.innerHTML = '<tr><td colspan="4" class="text-center">Loading...</td></tr>';

    try {
        const token = localStorage.getItem('auth_token');
        if (!token) {
            window.location.href = '/login';
            return;
        }
        
        const response = await fetch('/api/v1/images/get-images', {
            headers: getAuthHeaders()
        });
        
        if (handleApiError(response)) return;
        
        if (response.ok) {
            const images = await response.json();
            if (images.data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="4" class="text-center">No images found</td></tr>';
                return;
            }

            tbody.innerHTML = images.data.map(image => `
                <tr>
                    <td>${image.id || 'N/A'}</td>
                    <td><img src="${image.url}" alt="Image" style="width: 100px; height: 100px;"></td>
                    <td>${image.category_id || 'N/A'}</td>
                    <td>
                        <button class="btn btn-sm btn-primary btn-action" onclick="viewImage(${image.id})">View</button>
                        <button class="btn btn-sm btn-danger btn-action" onclick="deleteImage(${image.id})">Delete</button>
                    </td>
                </tr>
            `).join('');
        } else {
            const errorData = await response.json().catch(() => ({}));
            const errorMsg = errorData.detail || 'Error loading images';
            tbody.innerHTML = `<tr><td colspan="4" class="text-center text-danger">${errorMsg}</td></tr>`;
        }
    } catch (error) {
        console.error('Error loading images:', error);
        tbody.innerHTML = '<tr><td colspan="4" class="text-center text-danger">Error loading images</td></tr>';
    }
}

// Action functions (viewUser and deleteUser moved to users.js)

function viewCategory(categoryId) {
    alert(`View category ${categoryId} - Functionality to be implemented`);
}

function deleteCategory(categoryId) {
    if (confirm(`Are you sure you want to delete category ${categoryId}?`)) {
        alert(`Delete category ${categoryId} - Functionality to be implemented`);
    }
}

function viewImage(imageId) {
    alert(`View image ${imageId} - Functionality to be implemented`);
}

function deleteImage(imageId) {
    if (confirm(`Are you sure you want to delete image ${imageId}?`)) {
        alert(`Delete image ${imageId} - Functionality to be implemented`);
    }
}

