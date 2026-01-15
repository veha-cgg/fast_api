import { getUserData } from './auth.js';

document.addEventListener('DOMContentLoaded', function() {
    const token = localStorage.getItem('auth_token');
    if (!token) {
        window.location.href = '/login';
        return;
    }
    
    displayUserInfo();
});

function displayUserInfo() {
    const userData = getUserData();
    if (userData.email) {
        const welcomeSection = document.querySelector('.col-md-6');
        if (welcomeSection) {
            const userInfo = document.createElement('div');
            userInfo.className = 'alert alert-info mt-3';
            userInfo.innerHTML = `
                <strong>Welcome, ${userData.name || userData.email || 'User'}!</strong> 
                <span class="badge bg-primary">${userData.role || 'user'}</span>
            `;
            welcomeSection.insertBefore(userInfo, welcomeSection.querySelector('.d-flex'));
        }
        
        const authLink = document.getElementById('auth-link');
        if (authLink) {
            authLink.textContent = 'Logout';
            authLink.href = '#';
            authLink.onclick = function(e) {
                e.preventDefault();
                logout();
            };
        }
    }
}

function logout() {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_data');
    window.location.href = '/login';
}

