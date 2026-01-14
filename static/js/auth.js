// Authentication utility functions

// Token storage keys
const TOKEN_KEY = 'auth_token';
const USER_DATA_KEY = 'user_data';

// Get stored token
function getToken() {
    return localStorage.getItem(TOKEN_KEY);
}

// Store token
function setToken(token) {
    localStorage.setItem(TOKEN_KEY, token);
}

// Remove token
function removeToken() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_DATA_KEY);
}

// Get stored user data
function getUserData() {
    const userData = localStorage.getItem(USER_DATA_KEY);
    return userData ? JSON.parse(userData) : null;
}

// Store user data
function setUserData(userData) {
    localStorage.setItem(USER_DATA_KEY, JSON.stringify(userData));
}

// Check if user is authenticated
function isAuthenticated() {
    return getToken() !== null;
}

// Get authorization header
function getAuthHeaders() {
    const token = getToken();
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    };
}

// Logout function
function logout() {
    removeToken();
    window.location.href = '/login';
}

// Check authentication and redirect if not authenticated
function requireAuth() {
    if (!isAuthenticated()) {
        window.location.href = '/login';
        return false;
    }
    return true;
}

