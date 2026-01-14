document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    
    if (loginForm) {
        loginForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(loginForm);
            const email = formData.get('email');
            const password = formData.get('password');
            
            const submitButton = loginForm.querySelector('button[type="submit"]');
            const originalText = submitButton.textContent;
            submitButton.disabled = true;
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Loading...';
            
            try {
                const response = await fetch('/api/v1/login-json', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        email: email,
                        password: password
                    })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    if (data.token && data.token.access_token) {
                        localStorage.setItem('auth_token', data.token.access_token);
                    } else if (data.access_token) {
                        localStorage.setItem('auth_token', data.access_token);
                    }
                    
                    if (data.data) {
                        localStorage.setItem('user_data', JSON.stringify(data.data));
                    }
                    
                    window.location.href = '/panel';
                } else {
                    const errorMessage = data.detail || 'Login failed. Please check your credentials.';
                    showError(errorMessage);
                    submitButton.disabled = false;
                    submitButton.innerHTML = originalText;
                }
            } catch (error) {
                console.error('Login error:', error);
                showError('An error occurred during login. Please try again.');
                submitButton.disabled = false;
                submitButton.innerHTML = originalText;
            }
        });
    }
    
    if (localStorage.getItem('auth_token')) {
        window.location.href = '/panel';
    }
});

function showError(message) {
    const form = document.getElementById('loginForm');
    if (form) {
        const errorDiv = document.createElement('div');
        errorDiv.id = 'login-error';
        errorDiv.className = 'alert alert-danger mt-3';
        errorDiv.textContent = message;
        form.appendChild(errorDiv);
    }
}

