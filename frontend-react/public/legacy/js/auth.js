// ========================================
// ANEXI.AI - AUTHENTICATION LOGIC
// ========================================

// API URL - always use Nginx reverse proxy to the API Gateway
const API_URL = '/api';

// Toggle Password Visibility
function togglePassword() {
    const passwordInput = document.getElementById('password');
    const eyeIcon = document.querySelector('.toggle-password .eye-icon');
    
    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        eyeIcon.innerHTML = `
            <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
            <line x1="1" y1="1" x2="23" y2="23"></line>
        `;
    } else {
        passwordInput.type = 'password';
        eyeIcon.innerHTML = `
            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
            <circle cx="12" cy="12" r="3"></circle>
        `;
    }
}

// Password Strength Checker
function checkPasswordStrength(password) {
    const strengthBar = document.querySelector('.strength-fill');
    const strengthText = document.querySelector('.strength-text');
    
    if (!strengthBar) return;
    
    let strength = 0;
    
    if (password.length >= 8) strength += 25;
    if (password.match(/[a-z]/) && password.match(/[A-Z]/)) strength += 25;
    if (password.match(/[0-9]/)) strength += 25;
    if (password.match(/[^a-zA-Z0-9]/)) strength += 25;
    
    strengthBar.style.width = strength + '%';
    
    if (strength <= 25) {
        strengthBar.style.background = '#EF4444';
        strengthText.textContent = 'Weak password';
        strengthText.style.color = '#EF4444';
    } else if (strength <= 50) {
        strengthBar.style.background = '#F59E0B';
        strengthText.textContent = 'Fair password';
        strengthText.style.color = '#F59E0B';
    } else if (strength <= 75) {
        strengthBar.style.background = '#3B82F6';
        strengthText.textContent = 'Good password';
        strengthText.style.color = '#3B82F6';
    } else {
        strengthBar.style.background = '#10B981';
        strengthText.textContent = 'Strong password';
        strengthText.style.color = '#10B981';
    }
}

// Multi-step Form Navigation
function nextStep(stepNumber) {
    // Validate current step
    const currentStep = document.querySelector('.form-step.active');
    const currentStepNumber = Number(currentStep?.dataset?.step || 0);

    if (currentStepNumber === 2) {
        const selectedBusinessType = document.querySelector('input[name="businessType"]:checked');
        if (!selectedBusinessType) {
            showToast('Please select a business type', 'error');
            return;
        }
    }

    const inputs = currentStep.querySelectorAll('input[required]');
    let valid = true;
    
    inputs.forEach(input => {
        if (!input.value || (input.type === 'radio' && !document.querySelector(`input[name="${input.name}"]:checked`))) {
            valid = false;
            input.style.borderColor = '#EF4444';
            setTimeout(() => {
                input.style.borderColor = '';
            }, 2000);
        }
    });
    
    if (!valid) {
        showToast('Please fill all required fields', 'error');
        return;
    }
    
    // Update steps
    document.querySelectorAll('.form-step').forEach(step => {
        step.classList.remove('active');
    });
    
    document.querySelector(`.form-step[data-step="${stepNumber}"]`).classList.add('active');
    
    // Update progress
    document.querySelectorAll('.progress-step').forEach(step => {
        if (parseInt(step.dataset.step) <= stepNumber) {
            step.classList.add('active');
        } else {
            step.classList.remove('active');
        }
    });
}

function prevStep(stepNumber) {
    document.querySelectorAll('.form-step').forEach(step => {
        step.classList.remove('active');
    });
    
    document.querySelector(`.form-step[data-step="${stepNumber}"]`).classList.add('active');
    
    document.querySelectorAll('.progress-step').forEach(step => {
        if (parseInt(step.dataset.step) <= stepNumber) {
            step.classList.add('active');
        } else {
            step.classList.remove('active');
        }
    });
}

function initBusinessTypeSelection() {
    const businessCards = document.querySelectorAll('.radio-card');
    const businessInputs = document.querySelectorAll('input[name="businessType"]');
    if (!businessCards.length || !businessInputs.length) return;

    function syncBusinessSelection() {
        businessCards.forEach((card) => {
            const input = card.querySelector('input[name="businessType"]');
            card.classList.toggle('selected', !!input && input.checked);
        });
    }

    businessCards.forEach((card) => {
        card.addEventListener('click', () => {
            const input = card.querySelector('input[name="businessType"]');
            if (!input) return;
            input.checked = true;
            syncBusinessSelection();
        });
    });

    businessInputs.forEach((input) => {
        input.addEventListener('change', syncBusinessSelection);
    });

    syncBusinessSelection();
}

function buildApiUrl(path) {
    return `${API_URL}${path.startsWith('/') ? path : `/${path}`}`;
}

const SUPER_ADMIN_PATH = '/super-admin.html';

function normalizeRole(roleValue) {
    return String(roleValue || '').trim().toLowerCase();
}

function decodeTokenRole(token) {
    try {
        const base64Url = token.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const payload = JSON.parse(decodeURIComponent(atob(base64).split('').map(function (c) {
            return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
        }).join('')));
        return normalizeRole(payload?.role);
    } catch (e) {
        return '';
    }
}

function isAdminRole(roleValue) {
    const role = normalizeRole(roleValue);
    return role === 'admin' || role === 'super_admin' || role === 'founder';
}

async function resolveCurrentUserRole(token) {
    try {
        const response = await fetch(buildApiUrl('/auth/me'), {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
        });
        if (!response.ok) return '';
        const user = await response.json();
        return normalizeRole(user?.role);
    } catch (e) {
        return '';
    }
}

function getErrorMessageFromResponse(fallback, payload) {
    if (!payload) return fallback;
    if (typeof payload === 'string') return payload;
    if (typeof payload.detail === 'string') return payload.detail;
    if (typeof payload.message === 'string') return payload.message;
    return fallback;
}

async function parseResponseBody(response) {
    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('application/json')) {
        return response.json();
    }

    const text = await response.text();
    return text ? { detail: text } : null;
}

function startGoogleAuth(event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }

    window.location.assign(buildApiUrl('/auth/google/login'));
}

function handleOAuthRedirectResult() {
    const params = new URLSearchParams(window.location.search);
    const token = params.get('token');
    const userId = params.get('user_id');
    const firstLogin = params.get('first_login');
    const oauthError = params.get('oauth_error');

    if (oauthError) {
        showToast(decodeURIComponent(oauthError), 'error');
        params.delete('oauth_error');
        const qs = params.toString();
        window.history.replaceState({}, document.title, `${window.location.pathname}${qs ? `?${qs}` : ''}`);
        return;
    }

    if (!token) return;

    localStorage.setItem('access_token', token);
    if (userId) {
        localStorage.setItem('user_id', userId);
    }
    if (firstLogin === '1') {
        localStorage.setItem('show_payment_onboarding', '1');
        if (!localStorage.getItem('pending_plan')) {
            localStorage.setItem('pending_plan', 'starter');
        }
        if (!localStorage.getItem('onboarding_plan')) {
            localStorage.setItem('onboarding_plan', 'starter');
        }
    }

    params.delete('token');
    params.delete('user_id');
    params.delete('first_login');
    const qs = params.toString();
    window.history.replaceState({}, document.title, `${window.location.pathname}${qs ? `?${qs}` : ''}`);

    showToast('Google sign-in successful! Redirecting...', 'success');
    setTimeout(async () => {
        const roleFromToken = decodeTokenRole(token);
        const role = roleFromToken || await resolveCurrentUserRole(token);
        if (isAdminRole(role)) {
            window.location.href = SUPER_ADMIN_PATH;
            return;
        }
        if (firstLogin === '1') {
            const plan = localStorage.getItem('pending_plan') || 'starter';
            window.location.href = `dashboard.html#payment?plan=${encodeURIComponent(plan)}`;
            return;
        }
        window.location.href = 'dashboard.html';
    }, 800);
}

// Login Form Handler
document.addEventListener('DOMContentLoaded', function() {
    handleOAuthRedirectResult();
    initBusinessTypeSelection();

    if (window.location.pathname.includes('signup.html')) {
        const params = new URLSearchParams(window.location.search);
        const selectedPlan = (params.get('plan') || '').trim().toLowerCase();
        if (selectedPlan) {
            localStorage.setItem('onboarding_plan', selectedPlan);
            localStorage.setItem('pending_plan', selectedPlan);
        }
    }

    // Google social auth
    document.querySelectorAll('.btn-social').forEach(btn => {
        btn.addEventListener('click', function(event) {
            startGoogleAuth(event);
        });
    });

    const loginForm = document.getElementById('loginForm');
    
    if (loginForm) {
        loginForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const submitBtn = this.querySelector('.btn-submit');
            const btnText = submitBtn.querySelector('.btn-text');
            const btnLoader = submitBtn.querySelector('.btn-loader');
            
            // Show loading
            btnText.style.display = 'none';
            btnLoader.style.display = 'block';
            submitBtn.disabled = true;
            
            const formData = {
                email: document.getElementById('email').value,
                password: document.getElementById('password').value
            };
            
            try {
                const response = await fetch(buildApiUrl('/auth/login'), {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(formData)
                });
                
                const data = await parseResponseBody(response);
                
                if (response.ok) {
                    // Store token
                    localStorage.setItem('access_token', data.access_token);
                    localStorage.setItem('user_id', data.user_id);
                    sessionStorage.removeItem('logged_out');
                    sessionStorage.removeItem('logged_out_at');
                    
                    showToast('Login successful! Redirecting...', 'success');
                    
                    // Redirect to dashboard
                    setTimeout(async () => {
                        const roleFromToken = decodeTokenRole(data.access_token);
                        const role = roleFromToken || await resolveCurrentUserRole(data.access_token);
                        if (isAdminRole(role)) {
                            window.location.href = SUPER_ADMIN_PATH;
                            return;
                        }
                        const shouldOpenPayment = localStorage.getItem('show_payment_onboarding') === '1';
                        const plan = localStorage.getItem('pending_plan') || localStorage.getItem('onboarding_plan') || 'starter';
                        if (shouldOpenPayment) {
                            window.location.href = `dashboard.html#payment?plan=${encodeURIComponent(plan)}`;
                            return;
                        }
                        window.location.href = 'dashboard.html';
                    }, 1500);
                } else {
                    throw new Error(getErrorMessageFromResponse('Login failed', data));
                }
            } catch (error) {
                showToast(error.message, 'error');
                
                // Reset button
                btnText.style.display = 'block';
                btnLoader.style.display = 'none';
                submitBtn.disabled = false;
            }
        });
    }
    
    // Signup Form Handler
    const signupForm = document.getElementById('signupForm');
    
    if (signupForm) {
        // Password strength checker
        const passwordInput = document.getElementById('password');
        if (passwordInput) {
            passwordInput.addEventListener('input', function() {
                checkPasswordStrength(this.value);
            });
        }
        
        signupForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const submitBtn = this.querySelector('.btn-submit[type="submit"]');
            const btnText = submitBtn.querySelector('.btn-text');
            const btnLoader = submitBtn.querySelector('.btn-loader');
            
            // Show loading
            btnText.style.display = 'none';
            btnLoader.style.display = 'block';
            submitBtn.disabled = true;
            
            // Get form data
            const fullName = document.getElementById('fullName').value;
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const businessType = document.querySelector('input[name="businessType"]:checked')?.value;
            
            try {
                // Step 1: Create account
                const signupResponse = await fetch(buildApiUrl('/auth/signup'), {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        full_name: fullName,
                        email: email,
                        password: password,
                        role: 'user'
                    })
                });
                
                const signupData = await parseResponseBody(signupResponse);
                
                if (!signupResponse.ok) {
                    throw new Error(getErrorMessageFromResponse('Signup failed', signupData));
                }

                // Ensure first dashboard entry opens Payment section even if auto-login fails
                // and the user logs in manually right after signup.
                localStorage.setItem('show_payment_onboarding', '1');
                
                // Step 2: Set profile if business type is selected
                if (businessType) {
                    const profileResponse = await fetch(buildApiUrl('/auth/profile'), {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            user_id: signupData.user_id,
                            selling_type: businessType
                        })
                    });
                    
                    if (!profileResponse.ok) {
                        console.error('Profile creation failed');
                    }
                }
                
                // Step 3: Auto-login
                const loginResponse = await fetch(buildApiUrl('/auth/login'), {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        email: email,
                        password: password
                    })
                });
                
                const loginData = await parseResponseBody(loginResponse);
                
                if (loginResponse.ok) {
                    // Store token
                    localStorage.setItem('access_token', loginData.access_token);
                    localStorage.setItem('user_id', loginData.user_id);
                    sessionStorage.removeItem('logged_out');
                    sessionStorage.removeItem('logged_out_at');
                    
                    showToast('Account created successfully! Redirecting...', 'success');
                    
                    // Redirect to dashboard
                    setTimeout(() => {
                        const plan = localStorage.getItem('pending_plan') || localStorage.getItem('onboarding_plan');
                        const hash = plan ? `#payment?plan=${encodeURIComponent(plan)}` : '#payment';
                        window.location.href = 'dashboard.html' + hash;
                    }, 1500);
                } else {
                    showToast('Account created! Please login.', 'success');
                    setTimeout(() => {
                        window.location.href = 'login.html';
                    }, 1500);
                }
            } catch (error) {
                showToast(error.message, 'error');
                
                // Reset button
                btnText.style.display = 'block';
                btnLoader.style.display = 'none';
                submitBtn.disabled = false;
            }
        });
    }
});

// Toast Notification
function showToast(message, type = 'info') {
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.style.cssText = `
        position: fixed;
        top: 2rem;
        right: 2rem;
        background: ${type === 'success' ? '#10B981' : type === 'error' ? '#EF4444' : '#3B82F6'};
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
        z-index: 10000;
        animation: slideInRight 0.3s ease-out;
        font-weight: 600;
    `;
    toast.textContent = message;
    
    document.body.appendChild(toast);
    
    // Remove after 3 seconds
    setTimeout(() => {
        toast.style.animation = 'slideOutRight 0.3s ease-out';
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 300);
    }, 3000);
}

// Add animation keyframes
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Check if user is already logged in
async function checkAuth() {
    const onLoginPage = window.location.pathname.includes('login.html');
    if (onLoginPage && sessionStorage.getItem('logged_out') === '1') {
        try {
            // Keep user on login after explicit logout, even when pressing browser back.
            window.history.replaceState({ noBackExitsApp: true }, '', window.location.href);
            window.history.pushState({ noBackExitsApp: true }, '', window.location.href);
            window.addEventListener('popstate', function () {
                window.history.pushState({ noBackExitsApp: true }, '', window.location.href);
            });
            window.addEventListener('pageshow', function () {
                window.history.pushState({ noBackExitsApp: true }, '', window.location.href);
            });
        } catch (e) {
            // no-op
        }
    }

    const token = localStorage.getItem('access_token');
    if (token && (window.location.pathname.includes('login.html') || window.location.pathname.includes('signup.html'))) {
        const roleFromToken = decodeTokenRole(token);
        const role = roleFromToken || await resolveCurrentUserRole(token);
        if (isAdminRole(role)) {
            window.location.href = SUPER_ADMIN_PATH;
            return;
        }
        const shouldOpenPayment = localStorage.getItem('show_payment_onboarding') === '1';
        const plan = localStorage.getItem('pending_plan') || localStorage.getItem('onboarding_plan') || 'starter';
        if (shouldOpenPayment) {
            window.location.href = `dashboard.html#payment?plan=${encodeURIComponent(plan)}`;
            return;
        }
        window.location.href = 'dashboard.html';
    }
}

checkAuth();

