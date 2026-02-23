// Dashboard JavaScript

function hasValidLocalToken() {
    return !!(localStorage.getItem('access_token') || localStorage.getItem('token'));
}

function forceRedirectToLogin() {
    window.location.replace('login.html');
}

function enforceDashboardAuth() {
    if (!hasValidLocalToken()) {
        forceRedirectToLogin();
        return false;
    }
    return true;
}

function switchDashboardSection(sectionName) {
    const sectionId = `section-${sectionName}`;
    const target = document.getElementById(sectionId);
    if (!target) return;

    document.querySelectorAll('.dashboard-section').forEach((section) => {
        section.classList.toggle('active', section.id === sectionId);
    });

    document.querySelectorAll('.sidebar-nav .nav-item').forEach((item) => {
        item.classList.toggle('active', item.dataset.section === sectionName);
    });

    const titleEl = document.getElementById('sectionTitle');
    const subtitleEl = document.getElementById('sectionSubtitle');
    if (titleEl && subtitleEl) {
        const map = {
            dashboard: ['Dashboard', "Welcome back! Here's what's happening today."],
            profile: ['Profile', 'Manage personal info, security, notifications and system settings.'],
            orders: ['Orders', 'Manage and track your orders in one place.'],
            customers: ['Customers', 'Review customer records and engagement status.'],
            boutiques: ['Boutiques', 'Manage connected stores and channels.'],
            trust: ['Trust Layer', 'Inspect trust scoring and risk signals.'],
            analytics: ['Analytics', 'Monitor performance and business insights.'],
            payment: ['Payment', 'Handle subscription plan and checkout data.'],
            settings: ['Settings', 'Configure workspace preferences and account options.'],
        };
        const [title, subtitle] = map[sectionName] || map.dashboard;
        titleEl.textContent = title;
        subtitleEl.textContent = subtitle;
    }
}

// Guard immediate access before the rest of the dashboard logic runs.
if (window.location.pathname.includes('dashboard.html') && !hasValidLocalToken()) {
    forceRedirectToLogin();
}

// Toggle Sidebar Function - Make it global
window.toggleSidebar = function () {
    const sidebar = document.querySelector('.sidebar');
    const toggleBtn = document.querySelector('.sidebar-toggle-floating');

    if (sidebar) {
        sidebar.classList.toggle('collapsed');

        // Save state to localStorage
        const isCollapsed = sidebar.classList.contains('collapsed');
        localStorage.setItem('sidebarCollapsed', isCollapsed);

        console.log('Sidebar toggled:', isCollapsed ? 'collapsed' : 'expanded');
    }
}

// Logout function
window.logout = function () {
    localStorage.removeItem('access_token');
    localStorage.removeItem('token');
    localStorage.removeItem('user_id');
    localStorage.removeItem('sidebarCollapsed');
    sessionStorage.setItem('logged_out', '1');
    sessionStorage.setItem('logged_out_at', String(Date.now()));
    forceRedirectToLogin();
}

// Load User Profile
async function loadUserProfile() {
    const token = getAuthToken();
    if (!token) {
        console.log('No token found - redirecting to login');
        forceRedirectToLogin();
        return;
    }

    try {
        const response = await fetch('/api/auth/me', {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            const user = await response.json();
            const settings = await fetchProfileSettingsFromApi();
            updateUserProfile(settings || user);
        } else if (response.status === 401 || response.status === 403) {
            console.warn('Unauthorized profile request - forcing logout');
            window.logout();
            return;
        } else {
            console.error('Failed to load user profile:', response.status);
            // Don't redirect on error to prevent infinite loop
            // Just show a fallback
            updateUserProfile({
                user_id: null,
                email: 'user@anexi.ai',
                full_name: 'User',
                phone: '',
                avatar_url: '',
                role: 'user',
                notifications: {
                    order_updates: true,
                    risk_alerts: true,
                    email_digest: false,
                },
                system: {
                    language: 'en',
                    timezone: 'UTC',
                },
            });
        }
    } catch (error) {
        console.error('Error loading user profile:', error);
        // If network/auth state is broken, deny access by default.
        window.logout();
        return;
    }
}

// Parse JWT token - This function is no longer needed for user profile loading, but kept for other potential uses if any.
function parseJwt(token) {
    try {
        const base64Url = token.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const jsonPayload = decodeURIComponent(atob(base64).split('').map(function (c) {
            return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
        }).join(''));
        return JSON.parse(jsonPayload);
    } catch (e) {
        console.error('Error parsing JWT:', e);
        return null;
    }
}

let dashboardUserRecord = null;
let profileState = null;

function getInitials(text) {
    const source = (text || '').trim();
    if (!source) return 'AN';
    const parts = source.split(/\s+/);
    if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
    return `${parts[0][0] || ''}${parts[parts.length - 1][0] || ''}`.toUpperCase();
}

function buildDefaultProfileState(user) {
    return {
        full_name: user?.full_name || '',
        email: user?.email || '',
        phone: '',
        avatar_url: '',
        password_last_updated_at: '',
        notifications: {
            order_updates: true,
            risk_alerts: true,
            email_digest: false,
        },
        system: {
            language: 'en',
            timezone: 'UTC',
        },
    };
}

function mergeProfileState(user, saved) {
    const base = buildDefaultProfileState(user);
    const safeSaved = saved && typeof saved === 'object' ? saved : {};
    return {
        ...base,
        ...safeSaved,
        notifications: {
            ...base.notifications,
            ...(safeSaved.notifications || {}),
        },
        system: {
            ...base.system,
            ...(safeSaved.system || {}),
        },
    };
}

function getAuthToken() {
    return localStorage.getItem('access_token') || localStorage.getItem('token');
}

function authJsonHeaders() {
    const token = getAuthToken();
    return {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
    };
}

async function fetchProfileSettingsFromApi() {
    const token = getAuthToken();
    if (!token) return null;

    const response = await fetch('/api/auth/profile/settings', {
        headers: authJsonHeaders(),
    });
    if (!response.ok) {
        return null;
    }

    return response.json();
}

async function saveProfileSettingsToApi(patch) {
    const token = getAuthToken();
    if (!token) {
        throw new Error('You must be logged in.');
    }

    const response = await fetch('/api/auth/profile/settings', {
        method: 'PUT',
        headers: authJsonHeaders(),
        body: JSON.stringify(patch),
    });

    if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail || 'Failed to save profile settings');
    }

    return response.json();
}

async function updatePasswordToApi(currentPassword, newPassword) {
    const token = getAuthToken();
    if (!token) {
        throw new Error('You must be logged in.');
    }

    const response = await fetch('/api/auth/profile/password', {
        method: 'PUT',
        headers: authJsonHeaders(),
        body: JSON.stringify({
            current_password: currentPassword,
            new_password: newPassword,
        }),
    });

    if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail || 'Failed to update password');
    }

    return response.json();
}

function showProfileMessage(message, tone = 'info') {
    const el = document.getElementById('profileMessage');
    if (!el) return;
    el.textContent = message;

    if (tone === 'error') {
        el.style.color = '#fca5a5';
    } else if (tone === 'success') {
        el.style.color = '#86efac';
    } else {
        el.style.color = '';
    }
}

function updateAvatarUI() {
    const preview = document.getElementById('profileAvatarPreview');
    const image = document.getElementById('profileAvatarImage');
    const initials = document.getElementById('profileAvatarInitials');
    const sidebarAvatar = document.querySelector('.user-avatar');
    const sidebarInitials = document.getElementById('userInitials');
    const currentInitials = getInitials(profileState?.full_name || profileState?.email || 'AN');

    if (initials) initials.textContent = currentInitials;
    if (sidebarInitials) sidebarInitials.textContent = currentInitials;

    const hasAvatar = !!(profileState?.avatar_url || '').trim();
    if (hasAvatar) {
        if (image) {
            image.src = profileState.avatar_url;
            image.style.display = 'block';
        }
        if (initials) initials.style.display = 'none';
        if (sidebarAvatar) {
            sidebarAvatar.style.backgroundImage = `url('${profileState.avatar_url}')`;
            sidebarAvatar.style.backgroundSize = 'cover';
            sidebarAvatar.style.backgroundPosition = 'center';
        }
        if (sidebarInitials) sidebarInitials.style.display = 'none';
    } else {
        if (image) {
            image.removeAttribute('src');
            image.style.display = 'none';
        }
        if (initials) initials.style.display = '';
        if (sidebarAvatar) {
            sidebarAvatar.style.backgroundImage = '';
            sidebarAvatar.style.backgroundSize = '';
            sidebarAvatar.style.backgroundPosition = '';
        }
        if (sidebarInitials) sidebarInitials.style.display = '';
    }

    if (preview && !hasAvatar) {
        preview.style.backgroundImage = '';
    }
}

function syncSidebarProfileUI() {
    const userNameEl = document.getElementById('userName');
    const userEmailEl = document.getElementById('userEmail');
    if (userNameEl) {
        userNameEl.textContent = (profileState?.full_name || '').trim() || 'User';
    }
    if (userEmailEl) {
        userEmailEl.textContent = (profileState?.email || '').trim() || 'user@anexi.ai';
    }
    updateAvatarUI();
}

function fillProfileForms() {
    if (!profileState) return;
    const setVal = (id, value) => {
        const el = document.getElementById(id);
        if (el) el.value = value ?? '';
    };
    const setChecked = (id, value) => {
        const el = document.getElementById(id);
        if (el) el.checked = !!value;
    };

    setVal('profileNameInput', profileState.full_name);
    setVal('profileEmailInput', profileState.email);
    setVal('profilePhoneInput', profileState.phone);

    setChecked('notifOrderUpdates', profileState.notifications?.order_updates);
    setChecked('notifRiskAlerts', profileState.notifications?.risk_alerts);
    setChecked('notifEmailDigest', profileState.notifications?.email_digest);

    setVal('systemLanguage', profileState.system?.language || 'en');
    setVal('systemTimezone', profileState.system?.timezone || 'UTC');
    updateAvatarUI();
}

function activateProfileTab(tabName) {
    document.querySelectorAll('.profile-nav-item[data-profile-tab]').forEach((item) => {
        item.classList.toggle('active', item.dataset.profileTab === tabName);
    });

    document.querySelectorAll('.profile-panel').forEach((panel) => {
        panel.classList.toggle('active', panel.id === `profile-tab-${tabName}`);
    });
}

function initProfileSection() {
    if (window.__profileSectionInitialized) return;
    window.__profileSectionInitialized = true;

    document.querySelectorAll('.profile-nav-item[data-profile-tab]').forEach((item) => {
        item.addEventListener('click', () => {
            activateProfileTab(item.dataset.profileTab || 'personal');
        });
    });

    const avatarUploadBtn = document.getElementById('profileAvatarUploadBtn');
    const avatarInput = document.getElementById('profileAvatarInput');
    const avatarRemoveBtn = document.getElementById('profileAvatarRemoveBtn');

    if (avatarUploadBtn && avatarInput) {
        avatarUploadBtn.addEventListener('click', () => avatarInput.click());
        avatarInput.addEventListener('change', async (e) => {
            const file = e.target.files && e.target.files[0];
            if (!file || !profileState) return;
            if (!file.type.startsWith('image/')) {
                showProfileMessage('Please upload an image file for avatar.', 'error');
                return;
            }
            const reader = new FileReader();
            reader.onload = async () => {
                try {
                    const updated = await saveProfileSettingsToApi({
                        avatar_url: String(reader.result || ''),
                    });
                    updateUserProfile(updated);
                    showProfileMessage('Avatar updated successfully.', 'success');
                } catch (error) {
                    showProfileMessage(error.message || 'Failed to update avatar.', 'error');
                }
            };
            reader.readAsDataURL(file);
        });
    }

    if (avatarRemoveBtn) {
        avatarRemoveBtn.addEventListener('click', async () => {
            if (!profileState) return;
            try {
                const updated = await saveProfileSettingsToApi({ avatar_url: '' });
                updateUserProfile(updated);
                showProfileMessage('Avatar removed.', 'success');
            } catch (error) {
                showProfileMessage(error.message || 'Failed to remove avatar.', 'error');
            }
        });
    }

    const personalForm = document.getElementById('profilePersonalForm');
    if (personalForm) {
        personalForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            if (!profileState) return;

            const fullName = (document.getElementById('profileNameInput')?.value || '').trim();
            const email = (document.getElementById('profileEmailInput')?.value || '').trim();
            const phone = (document.getElementById('profilePhoneInput')?.value || '').trim();

            if (!fullName || !email) {
                showProfileMessage('Name and email are required.', 'error');
                return;
            }

            try {
                const updated = await saveProfileSettingsToApi({
                    full_name: fullName,
                    email,
                    phone,
                });
                updateUserProfile(updated);
                showProfileMessage('Personal information saved.', 'success');
            } catch (error) {
                showProfileMessage(error.message || 'Failed to save personal information.', 'error');
            }
        });
    }

    const profileDeleteBtn = document.getElementById('profileDeleteBtn');
    if (profileDeleteBtn) {
        profileDeleteBtn.addEventListener('click', async () => {
            if (!dashboardUserRecord) return;
            try {
                const updated = await saveProfileSettingsToApi({
                    full_name: dashboardUserRecord.full_name || '',
                    email: dashboardUserRecord.email || '',
                    phone: '',
                    avatar_url: '',
                    notifications: {
                        order_updates: true,
                        risk_alerts: true,
                        email_digest: false,
                    },
                    system: {
                        language: 'en',
                        timezone: 'UTC',
                    },
                });
                updateUserProfile(updated);
                showProfileMessage('Profile data reset to default.', 'success');
            } catch (error) {
                showProfileMessage(error.message || 'Failed to reset profile data.', 'error');
            }
        });
    }

    const securityForm = document.getElementById('profileSecurityForm');
    if (securityForm) {
        securityForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            if (!profileState) return;
            const current = document.getElementById('profileCurrentPasswordInput')?.value || '';
            const pw = document.getElementById('profilePasswordInput')?.value || '';
            const confirm = document.getElementById('profilePasswordConfirmInput')?.value || '';

            if (current.length < 8) {
                showProfileMessage('Current password is required.', 'error');
                return;
            }
            if (pw.length < 8) {
                showProfileMessage('Password must contain at least 8 characters.', 'error');
                return;
            }
            if (pw !== confirm) {
                showProfileMessage('Password confirmation does not match.', 'error');
                return;
            }

            try {
                await updatePasswordToApi(current, pw);
                securityForm.reset();
                showProfileMessage('Password updated.', 'success');
            } catch (error) {
                showProfileMessage(error.message || 'Failed to update password.', 'error');
            }
        });
    }

    const notifForm = document.getElementById('profileNotificationForm');
    if (notifForm) {
        notifForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            if (!profileState) return;
            try {
                const updated = await saveProfileSettingsToApi({
                    notifications: {
                        order_updates: !!document.getElementById('notifOrderUpdates')?.checked,
                        risk_alerts: !!document.getElementById('notifRiskAlerts')?.checked,
                        email_digest: !!document.getElementById('notifEmailDigest')?.checked,
                    },
                });
                updateUserProfile(updated);
                showProfileMessage('Notification settings saved.', 'success');
            } catch (error) {
                showProfileMessage(error.message || 'Failed to save notification settings.', 'error');
            }
        });
    }

    const systemForm = document.getElementById('profileSystemForm');
    if (systemForm) {
        systemForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            if (!profileState) return;
            try {
                const updated = await saveProfileSettingsToApi({
                    system: {
                        language: document.getElementById('systemLanguage')?.value || 'en',
                        timezone: document.getElementById('systemTimezone')?.value || 'UTC',
                    },
                });
                updateUserProfile(updated);
                showProfileMessage('System settings saved.', 'success');
            } catch (error) {
                showProfileMessage(error.message || 'Failed to save system settings.', 'error');
            }
        });
    }
}

function updateUserProfile(user) {
    dashboardUserRecord = {
        id: user?.id ?? user?.user_id ?? null,
        full_name: user?.full_name || '',
        email: user?.email || '',
        role: user?.role || 'user',
    };
    profileState = mergeProfileState(dashboardUserRecord, {
        full_name: user?.full_name,
        email: user?.email,
        phone: user?.phone || '',
        avatar_url: user?.avatar_url || '',
        notifications: user?.notifications,
        system: user?.system,
    });
    syncSidebarProfileUI();
    fillProfileForms();
    console.log('User profile updated:', profileState?.email || user?.email);
}

// Load Dashboard Data
async function loadDashboardData() {
    const token = localStorage.getItem('access_token') || localStorage.getItem('token');
    if (!token) {
        console.log('No token found for dashboard data');
        return;
    }

    try {
        // Fetch dashboard stats
        const response = await fetch('/api/dashboard/stats', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            updateDashboardStats(data);
        }
    } catch (error) {
        console.error('Error loading dashboard data:', error);
    }
}

function updateDashboardStats(data) {
    // Update stat values
    if (document.getElementById('totalOrders')) {
        document.getElementById('totalOrders').textContent = data.total_orders || 0;
    }
    if (document.getElementById('confirmedOrders')) {
        document.getElementById('confirmedOrders').textContent = data.confirmed_orders || 0;
    }
    if (document.getElementById('pendingOrders')) {
        document.getElementById('pendingOrders').textContent = data.pending_orders || 0;
    }
    if (document.getElementById('totalRevenue')) {
        document.getElementById('totalRevenue').textContent = `$${data.total_revenue || 0}`;
    }
}

window.addEventListener('pageshow', () => {
    enforceDashboardAuth();
});

window.addEventListener('popstate', () => {
    enforceDashboardAuth();
});

window.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') {
        enforceDashboardAuth();
    }
});

// Restore sidebar state on page load
function readDashboardRouteState() {
    const rawHash = (window.location.hash || '').replace(/^#/, '');
    if (!rawHash) return { section: '', plan: '' };

    const [sectionPart, queryPart] = rawHash.split('?');
    const section = (sectionPart || '').trim().toLowerCase();
    const params = new URLSearchParams(queryPart || '');
    const plan = (params.get('plan') || '').trim().toLowerCase();
    return { section, plan };
}

function setPaymentEmbedPlan(planKey) {
    const iframe = document.getElementById('paymentEmbed');
    if (!iframe) return;
    const safePlan = ['starter', 'growth', 'scale'].includes(planKey) ? planKey : 'starter';
    iframe.src = `payment.html?embed=1&plan=${encodeURIComponent(safePlan)}`;
}



const DASHBOARD_PLANS = {
    starter: { name: 'Starter', priceLabel: '$29/mo', amount: 29 },
    growth: { name: 'Growth', priceLabel: '$79/mo', amount: 79 },
    scale: { name: 'Scale', priceLabel: '$149/mo', amount: 149 },
};

let dashboardPaymentState = {
    planKey: 'starter',
    boutiqueId: null,
    customerId: null,
    initialized: false,
};

function formatPaymentCardNumber(value) {
    const digits = (value || '').replace(/\D/g, '').slice(0, 16);
    const padded = digits.padEnd(16, '0');
    return padded.match(/.{1,4}/g).join(' ');
}

function formatPaymentExpiry(value) {
    const digits = (value || '').replace(/\D/g, '').slice(0, 4);
    if (digits.length < 4) return '00/00';
    return `${digits.slice(0, 2)}/${digits.slice(2, 4)}`;
}

function updateDashboardPaymentLiveCard() {
    const name = document.getElementById('payHolderName')?.value?.trim() || 'CLIENT NAME';
    const number = document.getElementById('payCardNumber')?.value || '';
    const expiry = document.getElementById('payExpiry')?.value || '';
    const cvv = (document.getElementById('payCvv')?.value || '').replace(/\D/g, '').slice(0, 4) || '***';

    const nameEl = document.getElementById('liveCardName');
    const numberEl = document.getElementById('liveCardNumber');
    const expiryEl = document.getElementById('liveCardExpiry');
    const cvvEl = document.getElementById('liveCardCvv');
    if (nameEl) nameEl.textContent = name.toUpperCase().slice(0, 20);
    if (numberEl) numberEl.textContent = formatPaymentCardNumber(number);
    if (expiryEl) expiryEl.textContent = formatPaymentExpiry(expiry);
    if (cvvEl) cvvEl.textContent = cvv;
}

function updateDashboardPaymentPlanUI(planKey) {
    const safePlan = DASHBOARD_PLANS[planKey] ? planKey : 'starter';
    dashboardPaymentState.planKey = safePlan;
    localStorage.setItem('pending_plan', safePlan);
    localStorage.setItem('onboarding_plan', safePlan);

    document.querySelectorAll('#dashboardPackGrid .payment-pack-card').forEach((card) => {
        card.classList.toggle('active', card.dataset.plan === safePlan);
    });

    const summary = document.getElementById('paymentPlanSummary');
    const meta = document.getElementById('paymentPlanMeta');
    const plan = DASHBOARD_PLANS[safePlan];
    if (summary) {
        summary.childNodes[0].nodeValue = `Plan: ${plan.name} - ${plan.priceLabel}`;
    }
    if (meta) {
        if (dashboardPaymentState.boutiqueId && dashboardPaymentState.customerId) {
            meta.textContent = `Linked Boutique #${dashboardPaymentState.boutiqueId} | Customer #${dashboardPaymentState.customerId}`;
        }
    }
}

async function resolveDashboardPaymentContext() {
    const token = localStorage.getItem('access_token') || localStorage.getItem('token');
    const meta = document.getElementById('paymentPlanMeta');
    if (!token) {
        if (meta) meta.textContent = 'Not connected: payment preview only.';
        return;
    }

    try {
        const boutiqueRes = await fetch('/api/boutiques', {
            headers: { Authorization: `Bearer ${token}` },
        });
        if (!boutiqueRes.ok) {
            if (meta) meta.textContent = 'No boutique found. Create one before checkout.';
            return;
        }

        const boutiques = await boutiqueRes.json();
        if (!Array.isArray(boutiques) || !boutiques.length) {
            if (meta) meta.textContent = 'No boutique found. Create one before checkout.';
            return;
        }

        dashboardPaymentState.boutiqueId = boutiques[0].id;

        const customersRes = await fetch(`/api/boutiques/${dashboardPaymentState.boutiqueId}/customers`, {
            headers: { Authorization: `Bearer ${token}` },
        });
        if (!customersRes.ok) {
            if (meta) meta.textContent = `No customer linked to boutique #${dashboardPaymentState.boutiqueId}.`;
            return;
        }

        const customers = await customersRes.json();
        if (!Array.isArray(customers) || !customers.length) {
            if (meta) meta.textContent = `No customer linked to boutique #${dashboardPaymentState.boutiqueId}.`;
            return;
        }

        dashboardPaymentState.customerId = customers[0].id;
        if (meta) meta.textContent = `Linked Boutique #${dashboardPaymentState.boutiqueId} | Customer #${dashboardPaymentState.customerId}`;
    } catch (error) {
        if (meta) meta.textContent = 'Payment context unavailable.';
    }
}

function initDashboardPaymentSection(initialPlanKey) {
    if (dashboardPaymentState.initialized) {
        updateDashboardPaymentPlanUI(initialPlanKey || dashboardPaymentState.planKey);
        return;
    }

    const form = document.getElementById('dashboardPaymentForm');
    if (!form) return;

    dashboardPaymentState.initialized = true;

    ['payHolderName', 'payCardNumber', 'payExpiry', 'payCvv'].forEach((id) => {
        const input = document.getElementById(id);
        if (input) input.addEventListener('input', updateDashboardPaymentLiveCard);
    });

    document.querySelectorAll('#dashboardPackGrid .payment-pack-card button').forEach((btn) => {
        btn.addEventListener('click', () => {
            const plan = btn.closest('.payment-pack-card')?.dataset?.plan || 'starter';
            updateDashboardPaymentPlanUI(plan);
            window.location.hash = `payment?plan=${encodeURIComponent(plan)}`;
        });
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const token = localStorage.getItem('access_token') || localStorage.getItem('token');
        if (!token) {
            alert('Please login first.');
            return;
        }

        if (!dashboardPaymentState.boutiqueId || !dashboardPaymentState.customerId) {
            alert('No linked boutique/customer found for payment.');
            return;
        }

        const plan = DASHBOARD_PLANS[dashboardPaymentState.planKey] || DASHBOARD_PLANS.starter;
        try {
            const res = await fetch('/api/payments/checkout', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify({
                    boutique_id: dashboardPaymentState.boutiqueId,
                    customer_id: dashboardPaymentState.customerId,
                    plan: plan.name.toLowerCase(),
                    amount: plan.amount,
                    payment_method: 'card',
                }),
            });

            if (!res.ok) {
                const err = await res.text();
                throw new Error(err || 'Checkout failed');
            }

            alert(`Paiement confirme pour ${plan.name}.`);
        } catch (error) {
            alert('Payment failed. Please verify your setup.');
        }
    });

    updateDashboardPaymentPlanUI(initialPlanKey || dashboardPaymentState.planKey);
    updateDashboardPaymentLiveCard();
    resolveDashboardPaymentContext();
}
function applySectionFromHash() {
    const route = readDashboardRouteState();
    const section = route.section || 'dashboard';

    let activePaymentPlan = route.plan
        || (localStorage.getItem('pending_plan') || '').trim().toLowerCase()
        || (localStorage.getItem('onboarding_plan') || '').trim().toLowerCase();

    if (!['starter', 'growth', 'scale'].includes(activePaymentPlan)) {
        activePaymentPlan = 'starter';
    }

    switchDashboardSection(section);

    if (section === 'payment') {
        setPaymentEmbedPlan(activePaymentPlan);
    }
}
window.addEventListener('DOMContentLoaded', () => {
    if (!enforceDashboardAuth()) return;

    const isCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
    const sidebar = document.querySelector('.sidebar');
    if (isCollapsed && sidebar) {
        sidebar.classList.add('collapsed');
    }

    const toggleBtn = document.getElementById('sidebarToggleBtn');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', window.toggleSidebar);
        console.log('Toggle button event listener attached');
    }

    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function (e) {
            e.preventDefault();
            console.log('Logout button clicked');
            window.logout();
        });
        console.log('Logout button event listener attached');
    } else {
        console.error('Logout button not found!');
    }

    initProfileSection();
    loadUserProfile();
    loadDashboardData();

    const showPaymentOnboarding = localStorage.getItem('show_payment_onboarding') === '1';
    let route = readDashboardRouteState();

    let activePaymentPlan = route.plan
        || (localStorage.getItem('pending_plan') || '').trim().toLowerCase()
        || (localStorage.getItem('onboarding_plan') || '').trim().toLowerCase();

    if (!['starter', 'growth', 'scale'].includes(activePaymentPlan)) {
        activePaymentPlan = 'starter';
    }

    document.querySelectorAll('.sidebar-nav .nav-item[data-section]').forEach((item) => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const sectionName = item.dataset.section || 'dashboard';

            if (sectionName === 'payment') {
                const planForRoute = activePaymentPlan || 'starter';
                setPaymentEmbedPlan(planForRoute);
                window.location.hash = `payment?plan=${encodeURIComponent(planForRoute)}`;
                return;
            }

            window.location.hash = sectionName;
        });
    });

    if (showPaymentOnboarding) {
        history.replaceState({}, '', `dashboard.html#payment?plan=${encodeURIComponent(activePaymentPlan)}`);
        localStorage.removeItem('show_payment_onboarding');
        route = readDashboardRouteState();
    }

    let initialSection = route.section || 'dashboard';

    switchDashboardSection(initialSection);
    window.addEventListener('hashchange', applySectionFromHash);

    if (initialSection === 'payment') {
        setPaymentEmbedPlan(activePaymentPlan);
        history.replaceState({}, '', `dashboard.html#payment?plan=${encodeURIComponent(activePaymentPlan)}`);
    }
});

console.log('Dashboard loaded - toggleSidebar function ready');





