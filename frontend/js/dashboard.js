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

    if (sectionName === 'trust') {
        loadTrustSection();
    }
    if (sectionName === 'analytics') {
        loadAnalyticsSection();
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
            await loadDashboardCharts();
            await loadDashboardTrustLinkage();
        }
    } catch (error) {
        console.error('Error loading dashboard data:', error);
    }
}

let trustSectionLoaded = false;
let trustSectionLoading = false;
const TRUST_PAGE_SIZE = 25;
const trustState = {
    page: 0,
    activePane: 'overview',
    filters: {
        segment: '',
        campaign_id: '',
        score_range: '',
        sort: 'date_desc',
    },
    expandedInteractionId: '',
    summary: null,
    timeline: null,
    charts: {
        scoreTrend: null,
        riskTrend: null,
        campaignScore: null,
        campaignRisk: null,
    },
};

let dashboardRevenueChart = null;
let dashboardOrderStatusChart = null;
let analyticsSectionLoaded = false;
let analyticsSectionLoading = false;
const analyticsState = {
    selectedCampaign: '',
    charts: {
        campaignScore: null,
        campaignRisk: null,
    },
};

function trustHeaders() {
    const token = getAuthToken();
    return {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
    };
}

function escapeHtml(value) {
    return String(value ?? '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#39;');
}

function formatDateTime(value) {
    if (!value) return '-';
    const dt = new Date(value);
    if (Number.isNaN(dt.getTime())) return '-';
    return dt.toLocaleString();
}

function metricCard(label, value) {
    return `
        <div style="border:1px solid var(--glass-border);border-radius:12px;padding:.7rem .8rem;background:rgba(255,255,255,.04);">
            <div style="font-size:.78rem;color:var(--text-muted);">${escapeHtml(label)}</div>
            <div style="font-size:1.15rem;font-weight:700;color:var(--text-primary);margin-top:.2rem;">${escapeHtml(value)}</div>
        </div>
    `;
}

function segmentBadge(segment) {
    const map = {
        HIGH_TRUST: '#22c55e',
        STABLE: '#3b82f6',
        RISK: '#f59e0b',
        HIGH_RISK: '#ef4444',
    };
    const color = map[segment] || '#9ca3af';
    return `<span style="display:inline-block;border:1px solid ${color};color:${color};padding:.2rem .45rem;border-radius:999px;font-size:.78rem;font-weight:700;">${escapeHtml(segment)}</span>`;
}

function renderTrustShell() {
    const section = document.getElementById('section-trust');
    if (!section) return;

    section.innerHTML = `
        <div class="section-placeholder trust-layer-shell">
            <div class="trust-layer-head">
                <h3>Trust Layer</h3>
                <p id="trustStatusLine">Loading trust data...</p>
            </div>

            <div class="trust-switchbar">
                <button type="button" class="trust-tab-btn ${trustState.activePane === 'overview' ? 'active' : ''}" data-trust-pane="overview">Overview</button>
                <button type="button" class="trust-tab-btn ${trustState.activePane === 'campaigns' ? 'active' : ''}" data-trust-pane="campaigns">Campaigns</button>
                <button type="button" class="trust-tab-btn ${trustState.activePane === 'interactions' ? 'active' : ''}" data-trust-pane="interactions">Interactions</button>
                <button type="button" class="trust-tab-btn ${trustState.activePane === 'analysis' ? 'active' : ''}" data-trust-pane="analysis">Analysis</button>
            </div>

            <div id="trustPane-overview" class="trust-pane ${trustState.activePane === 'overview' ? 'active' : ''}">
                <div id="trustSummaryGrid" class="trust-kpi-grid"></div>
                <div class="trust-card-block">
                    <h4>Segment Distribution</h4>
                    <div id="trustSegments" class="trust-chip-list"></div>
                </div>
            </div>

            <div id="trustPane-campaigns" class="trust-pane ${trustState.activePane === 'campaigns' ? 'active' : ''}">
                <div class="trust-card-block">
                    <h4>Campaign Performance</h4>
                    <div class="trust-table-wrap">
                        <table class="trust-table trust-table-campaigns">
                            <thead>
                                <tr>
                                    <th>campaign_id</th>
                                    <th>total_interactions</th>
                                    <th>avg_score</th>
                                    <th>high_risk_rate</th>
                                    <th>dominant_segment</th>
                                </tr>
                            </thead>
                            <tbody id="trustCampaignRows"></tbody>
                        </table>
                    </div>
                </div>
            </div>

            <div id="trustPane-interactions" class="trust-pane ${trustState.activePane === 'interactions' ? 'active' : ''}">
                <div class="trust-card-block">
                    <h4>Recent / All Trust Interactions</h4>
                    <div class="trust-filter-row">
                        <select id="trustFilterSegment" class="trust-select">
                            <option value="">All segments</option>
                            <option value="HIGH_TRUST">HIGH_TRUST</option>
                            <option value="STABLE">STABLE</option>
                            <option value="RISK">RISK</option>
                            <option value="HIGH_RISK">HIGH_RISK</option>
                        </select>
                        <select id="trustFilterCampaign" class="trust-select">
                            <option value="">All campaigns</option>
                        </select>
                        <select id="trustFilterScore" class="trust-select">
                            <option value="">All scores</option>
                            <option value="0-39">0-39</option>
                            <option value="40-59">40-59</option>
                            <option value="60-79">60-79</option>
                            <option value="80-100">80-100</option>
                        </select>
                        <select id="trustSort" class="trust-select">
                            <option value="date_desc">Date desc</option>
                            <option value="date_asc">Date asc</option>
                            <option value="score_desc">Score desc</option>
                            <option value="score_asc">Score asc</option>
                        </select>
                    </div>
                    <div class="trust-table-wrap">
                        <table class="trust-table trust-table-interactions">
                            <thead>
                                <tr>
                                    <th>order_id</th>
                                    <th>client_name</th>
                                    <th>product_name</th>
                                    <th>campaign_id</th>
                                    <th>confirmation_status</th>
                                    <th>call_duration</th>
                                    <th>hesitation_score</th>
                                    <th>interaction_score</th>
                                    <th>segment</th>
                                    <th>recommended_action</th>
                                    <th>created_at</th>
                                </tr>
                            </thead>
                            <tbody id="trustInteractionsRows"></tbody>
                        </table>
                    </div>
                    <div class="trust-pager">
                        <span id="trustPagerInfo"></span>
                        <div class="trust-pager-actions">
                            <button id="trustPrevPage" type="button" class="profile-btn">Prev</button>
                            <button id="trustNextPage" type="button" class="profile-btn">Next</button>
                        </div>
                    </div>
                </div>
            </div>

            <div id="trustPane-analysis" class="trust-pane ${trustState.activePane === 'analysis' ? 'active' : ''}">
                <div class="trust-card-block">
                    <h4>Trust Score Trend (Last 14 Days)</h4>
                    <div style="min-height:240px;">
                        <canvas id="trustScoreTrendChart"></canvas>
                    </div>
                </div>
                <div class="trust-card-block">
                    <h4>High Risk vs Total Interactions (Last 14 Days)</h4>
                    <div style="min-height:240px;">
                        <canvas id="trustRiskTrendChart"></canvas>
                    </div>
                </div>
                <div class="trust-card-block">
                    <h4>Campaign Avg Score</h4>
                    <div style="min-height:240px;">
                        <canvas id="trustCampaignScoreChart"></canvas>
                    </div>
                </div>
                <div class="trust-card-block">
                    <h4>Campaign High Risk Rate</h4>
                    <div style="min-height:240px;">
                        <canvas id="trustCampaignRiskChart"></canvas>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function switchTrustPane(pane) {
    trustState.activePane = pane || 'overview';
    document.querySelectorAll('.trust-tab-btn[data-trust-pane]').forEach((btn) => {
        btn.classList.toggle('active', btn.dataset.trustPane === trustState.activePane);
    });
    document.querySelectorAll('.trust-pane').forEach((paneEl) => {
        paneEl.classList.toggle('active', paneEl.id === `trustPane-${trustState.activePane}`);
    });

    // Chart.js can render blank when initialized inside display:none containers.
    // Repaint charts after Analysis tab becomes visible.
    if (trustState.activePane === 'analysis') {
        setTimeout(() => {
            if (trustState.timeline) {
                renderTrustTimelineCharts(trustState.timeline);
            }
            if (trustState.summary) {
                renderTrustCampaignCharts(trustState.summary);
            }
        }, 0);
    }
}

function parseScoreRange(rangeValue) {
    if (!rangeValue) return { score_min: null, score_max: null };
    const parts = String(rangeValue).split('-');
    if (parts.length !== 2) return { score_min: null, score_max: null };
    const scoreMin = Number(parts[0]);
    const scoreMax = Number(parts[1]);
    if (Number.isNaN(scoreMin) || Number.isNaN(scoreMax)) return { score_min: null, score_max: null };
    return { score_min: scoreMin, score_max: scoreMax };
}

function syncTrustFilterControls() {
    const segmentEl = document.getElementById('trustFilterSegment');
    const campaignEl = document.getElementById('trustFilterCampaign');
    const scoreEl = document.getElementById('trustFilterScore');
    const sortEl = document.getElementById('trustSort');
    if (segmentEl) segmentEl.value = trustState.filters.segment || '';
    if (campaignEl) campaignEl.value = trustState.filters.campaign_id || '';
    if (scoreEl) scoreEl.value = trustState.filters.score_range || '';
    if (sortEl) sortEl.value = trustState.filters.sort || 'date_desc';
}

function bindTrustEvents() {
    const trustTabButtons = document.querySelectorAll('.trust-tab-btn[data-trust-pane]');
    const segmentEl = document.getElementById('trustFilterSegment');
    const campaignEl = document.getElementById('trustFilterCampaign');
    const scoreEl = document.getElementById('trustFilterScore');
    const sortEl = document.getElementById('trustSort');
    const prevBtn = document.getElementById('trustPrevPage');
    const nextBtn = document.getElementById('trustNextPage');
    const interactionsRows = document.getElementById('trustInteractionsRows');

    trustTabButtons.forEach((btn) => {
        btn.addEventListener('click', () => {
            switchTrustPane(btn.dataset.trustPane || 'overview');
        });
    });

    if (segmentEl) {
        segmentEl.addEventListener('change', () => {
            trustState.filters.segment = segmentEl.value || '';
            trustState.page = 0;
            refreshTrustInteractions();
        });
    }
    if (campaignEl) {
        campaignEl.addEventListener('change', () => {
            trustState.filters.campaign_id = campaignEl.value || '';
            trustState.page = 0;
            refreshTrustInteractions();
        });
    }
    if (scoreEl) {
        scoreEl.addEventListener('change', () => {
            trustState.filters.score_range = scoreEl.value || '';
            trustState.page = 0;
            refreshTrustInteractions();
        });
    }
    if (sortEl) {
        sortEl.addEventListener('change', () => {
            trustState.filters.sort = sortEl.value || 'date_desc';
            trustState.page = 0;
            refreshTrustInteractions();
        });
    }
    if (prevBtn) {
        prevBtn.addEventListener('click', () => {
            if (trustState.page <= 0) return;
            trustState.page -= 1;
            refreshTrustInteractions();
        });
    }
    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            trustState.page += 1;
            refreshTrustInteractions();
        });
    }
    if (interactionsRows) {
        interactionsRows.addEventListener('click', (event) => {
            const row = event.target.closest('tr[data-interaction-id]');
            if (!row) return;
            const id = row.dataset.interactionId || '';
            trustState.expandedInteractionId = trustState.expandedInteractionId === id ? '' : id;
            document.querySelectorAll('tr[data-detail-for]').forEach((detail) => {
                detail.style.display = detail.dataset.detailFor === trustState.expandedInteractionId ? '' : 'none';
            });
        });
    }
}

function applyCampaignFilterFromRow(campaignId) {
    trustState.filters.campaign_id = campaignId || '';
    trustState.page = 0;
    syncTrustFilterControls();
    switchTrustPane('interactions');
    refreshTrustInteractions();
}

function renderCampaignRows(summary) {
    const rowsEl = document.getElementById('trustCampaignRows');
    if (!rowsEl) return;
    const rows = Array.isArray(summary?.by_campaign) ? summary.by_campaign : [];
    if (!rows.length) {
        rowsEl.innerHTML = `<tr><td colspan="5" style="padding:.55rem;color:var(--text-muted);">No campaign data yet.</td></tr>`;
        return;
    }
    rowsEl.innerHTML = rows.map((row) => `
        <tr data-campaign-id="${escapeHtml(row.campaign_id)}" style="border-bottom:1px solid var(--glass-border);cursor:pointer;">
            <td style="padding:.5rem;color:var(--text-primary);">${escapeHtml(row.campaign_id)}</td>
            <td style="padding:.5rem;color:var(--text-secondary);">${escapeHtml(row.total_interactions)}</td>
            <td style="padding:.5rem;color:var(--text-secondary);">${escapeHtml(row.avg_interaction_score)}</td>
            <td style="padding:.5rem;color:var(--text-secondary);">${escapeHtml(row.high_risk_rate)}%</td>
            <td style="padding:.5rem;color:var(--text-secondary);">${segmentBadge(row.dominant_segment)}</td>
        </tr>
    `).join('');

    rowsEl.querySelectorAll('tr[data-campaign-id]').forEach((tr) => {
        tr.addEventListener('click', () => {
            applyCampaignFilterFromRow(tr.dataset.campaignId || '');
        });
    });
}

function renderSummary(summary) {
    trustState.summary = summary;
    const statusLine = document.getElementById('trustStatusLine');
    const summaryGrid = document.getElementById('trustSummaryGrid');
    const segmentsEl = document.getElementById('trustSegments');
    const campaignFilterEl = document.getElementById('trustFilterCampaign');

    if (summaryGrid) {
        summaryGrid.innerHTML = [
            metricCard('Total interactions', summary.total_interactions ?? 0),
            metricCard('Avg score', summary.avg_interaction_score ?? 0),
            metricCard('High risk rate', `${summary.high_risk_rate ?? 0}%`),
            metricCard('HIGH_RISK count', summary.high_risk_count ?? 0),
            metricCard('HIGH_TRUST count', summary.high_trust_count ?? 0),
            metricCard('Last interaction', formatDateTime(summary.last_interaction_at)),
        ].join('');
    }
    if (segmentsEl) {
        const segments = Array.isArray(summary.segments) ? summary.segments : [];
        segmentsEl.innerHTML = segments.length
            ? segments.map((s) => `<span style="border:1px solid var(--glass-border);padding:.35rem .55rem;border-radius:10px;background:rgba(255,255,255,.04);font-size:.82rem;color:var(--text-secondary);">${escapeHtml(s.segment)}: <strong style="color:var(--text-primary);">${escapeHtml(s.total)}</strong> (${escapeHtml(s.percentage)}%)</span>`).join('')
            : `<span style="color:var(--text-muted);font-size:.9rem;">No segment data yet.</span>`;
    }
    renderCampaignRows(summary);
    renderTrustCampaignCharts(summary);

    if (campaignFilterEl) {
        const previousValue = trustState.filters.campaign_id || '';
        const campaignRows = Array.isArray(summary.by_campaign) ? summary.by_campaign : [];
        campaignFilterEl.innerHTML = `<option value="">All campaigns</option>${campaignRows.map((row) => `<option value="${escapeHtml(row.campaign_id)}">${escapeHtml(row.campaign_id)}</option>`).join('')}`;
        trustState.filters.campaign_id = previousValue;
    }

    if (statusLine) {
        statusLine.textContent = 'Trust metrics loaded.';
    }
    syncTrustFilterControls();
}

function renderInteractionRows(pageData) {
    const rowsEl = document.getElementById('trustInteractionsRows');
    const pagerInfo = document.getElementById('trustPagerInfo');
    const prevBtn = document.getElementById('trustPrevPage');
    const nextBtn = document.getElementById('trustNextPage');
    if (!rowsEl || !pagerInfo) return;

    const items = Array.isArray(pageData?.items) ? pageData.items : [];
    const total = Number(pageData?.total || 0);
    const offset = Number(pageData?.offset || 0);
    const hasNext = !!pageData?.has_next;
    const start = total === 0 ? 0 : offset + 1;
    const end = offset + items.length;
    pagerInfo.textContent = `Showing ${start}-${end} of ${total}`;
    if (prevBtn) prevBtn.disabled = trustState.page <= 0;
    if (nextBtn) nextBtn.disabled = !hasNext;

    if (!items.length) {
        rowsEl.innerHTML = `<tr><td colspan="11" style="padding:.7rem;color:var(--text-muted);">No trust evaluations yet. Run /internal/trust/evaluate to start.</td></tr>`;
        return;
    }

    rowsEl.innerHTML = items.map((row) => {
        const rowId = escapeHtml(row.id);
        const isExpanded = trustState.expandedInteractionId === row.id;
        return `
            <tr data-interaction-id="${rowId}" style="border-bottom:1px solid var(--glass-border);cursor:pointer;">
                <td style="padding:.45rem;color:var(--text-primary);">${escapeHtml(row.order_id)}</td>
                <td style="padding:.45rem;color:var(--text-secondary);">${escapeHtml(row.client_name || '-')}</td>
                <td style="padding:.45rem;color:var(--text-secondary);">${escapeHtml(row.product_name || '-')}</td>
                <td style="padding:.45rem;color:var(--text-secondary);">${escapeHtml(row.campaign_id || '-')}</td>
                <td style="padding:.45rem;color:var(--text-secondary);">${escapeHtml(row.confirmation_status)}</td>
                <td style="padding:.45rem;color:var(--text-secondary);">${escapeHtml(row.call_duration)}</td>
                <td style="padding:.45rem;color:var(--text-secondary);">${escapeHtml(row.hesitation_score)}</td>
                <td style="padding:.45rem;color:var(--text-secondary);">${escapeHtml(row.interaction_score)}</td>
                <td style="padding:.45rem;color:var(--text-secondary);">${segmentBadge(row.segment)}</td>
                <td style="padding:.45rem;color:var(--text-secondary);">${escapeHtml(row.recommended_action)}</td>
                <td style="padding:.45rem;color:var(--text-secondary);">${escapeHtml(formatDateTime(row.created_at))}</td>
            </tr>
            <tr data-detail-for="${rowId}" style="display:${isExpanded ? '' : 'none'};background:rgba(255,255,255,.02);">
                <td colspan="11" style="padding:.6rem;border-bottom:1px solid var(--glass-border);">
                    <div style="color:var(--text-primary);font-weight:600;margin-bottom:.35rem;">Interaction Detail</div>
                    <div style="font-size:.82rem;color:var(--text-secondary);line-height:1.5;">
                        Score breakdown:
                        confirmation=${escapeHtml(row.score_breakdown?.confirmation_component ?? 0)},
                        duration=${escapeHtml(row.score_breakdown?.duration_component ?? 0)},
                        hesitation=${escapeHtml(row.score_breakdown?.hesitation_component ?? 0)}.
                        Segment=${escapeHtml(row.segment)}.
                        Recommended action=${escapeHtml(row.recommended_action)}.
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

function destroyTrustCharts() {
    if (trustState.charts.scoreTrend) {
        trustState.charts.scoreTrend.destroy();
        trustState.charts.scoreTrend = null;
    }
    if (trustState.charts.riskTrend) {
        trustState.charts.riskTrend.destroy();
        trustState.charts.riskTrend = null;
    }
    if (trustState.charts.campaignScore) {
        trustState.charts.campaignScore.destroy();
        trustState.charts.campaignScore = null;
    }
    if (trustState.charts.campaignRisk) {
        trustState.charts.campaignRisk.destroy();
        trustState.charts.campaignRisk = null;
    }
}

function renderTrustCampaignCharts(summary) {
    if (typeof Chart === 'undefined') return;
    const scoreCanvas = document.getElementById('trustCampaignScoreChart');
    const riskCanvas = document.getElementById('trustCampaignRiskChart');
    if (!scoreCanvas || !riskCanvas) return;

    const campaigns = Array.isArray(summary?.by_campaign) ? summary.by_campaign : [];
    const labels = campaigns.map((row) => row.campaign_id);
    const scores = campaigns.map((row) => Number(row.avg_interaction_score || 0));
    const risks = campaigns.map((row) => Number(row.high_risk_rate || 0));

    if (trustState.charts.campaignScore) trustState.charts.campaignScore.destroy();
    trustState.charts.campaignScore = new Chart(scoreCanvas.getContext('2d'), {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label: 'Avg Score',
                data: scores,
                backgroundColor: 'rgba(99, 102, 241, 0.45)',
                borderColor: 'rgba(99, 102, 241, 0.9)',
                borderWidth: 1,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { labels: { color: '#94a3b8' } } },
            scales: {
                x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(148,163,184,0.12)' } },
                y: { min: 0, max: 100, ticks: { color: '#94a3b8' }, grid: { color: 'rgba(148,163,184,0.12)' } },
            },
        },
    });

    if (trustState.charts.campaignRisk) trustState.charts.campaignRisk.destroy();
    trustState.charts.campaignRisk = new Chart(riskCanvas.getContext('2d'), {
        type: 'line',
        data: {
            labels,
            datasets: [{
                label: 'High Risk Rate %',
                data: risks,
                borderColor: '#ef4444',
                backgroundColor: 'rgba(239, 68, 68, 0.18)',
                fill: true,
                tension: 0.35,
                pointRadius: 3,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { labels: { color: '#94a3b8' } } },
            scales: {
                x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(148,163,184,0.12)' } },
                y: { min: 0, max: 100, ticks: { color: '#94a3b8' }, grid: { color: 'rgba(148,163,184,0.12)' } },
            },
        },
    });
}

function renderTrustTimelineCharts(timeline) {
    if (typeof Chart === 'undefined') return;
    const scoreCanvas = document.getElementById('trustScoreTrendChart');
    const riskCanvas = document.getElementById('trustRiskTrendChart');
    if (!scoreCanvas || !riskCanvas) return;

    destroyTrustCharts();

    trustState.charts.scoreTrend = new Chart(scoreCanvas.getContext('2d'), {
        type: 'line',
        data: {
            labels: timeline.labels || [],
            datasets: [
                {
                    label: 'Avg Interaction Score',
                    data: timeline.avg_interaction_score || [],
                    borderColor: '#7c3aed',
                    backgroundColor: 'rgba(124, 58, 237, 0.15)',
                    tension: 0.35,
                    fill: true,
                    pointRadius: 3,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { labels: { color: '#94a3b8' } } },
            scales: {
                x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(148,163,184,0.15)' } },
                y: { min: 0, max: 100, ticks: { color: '#94a3b8' }, grid: { color: 'rgba(148,163,184,0.15)' } },
            },
        },
    });

    trustState.charts.riskTrend = new Chart(riskCanvas.getContext('2d'), {
        data: {
            labels: timeline.labels || [],
            datasets: [
                {
                    type: 'bar',
                    label: 'Total Interactions',
                    data: timeline.total_interactions || [],
                    backgroundColor: 'rgba(59, 130, 246, 0.35)',
                    borderColor: 'rgba(59, 130, 246, 0.8)',
                    borderWidth: 1,
                },
                {
                    type: 'line',
                    label: 'High Risk Count',
                    data: timeline.high_risk_count || [],
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.2)',
                    tension: 0.35,
                    pointRadius: 3,
                    yAxisID: 'y',
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { labels: { color: '#94a3b8' } } },
            scales: {
                x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(148,163,184,0.15)' } },
                y: { beginAtZero: true, ticks: { color: '#94a3b8' }, grid: { color: 'rgba(148,163,184,0.15)' } },
            },
        },
    });
}

async function refreshTrustSummary() {
    const response = await fetch('/api/trust/metrics/summary', { headers: trustHeaders() });
    if (!response.ok) throw new Error(`Trust summary API error (${response.status})`);
    const summary = await response.json();
    renderSummary(summary);
}

async function refreshTrustTimeline() {
    const response = await fetch('/api/trust/metrics/timeline?days=14', { headers: trustHeaders() });
    if (!response.ok) throw new Error(`Trust timeline API error (${response.status})`);
    const timeline = await response.json();
    trustState.timeline = timeline;
    renderTrustTimelineCharts(timeline);
}

async function refreshTrustInteractions() {
    const statusLine = document.getElementById('trustStatusLine');
    const { score_min, score_max } = parseScoreRange(trustState.filters.score_range);
    const params = new URLSearchParams();
    params.set('limit', String(TRUST_PAGE_SIZE));
    params.set('offset', String(trustState.page * TRUST_PAGE_SIZE));
    params.set('sort', trustState.filters.sort || 'date_desc');
    if (trustState.filters.segment) params.set('segment', trustState.filters.segment);
    if (trustState.filters.campaign_id) params.set('campaign_id', trustState.filters.campaign_id);
    if (score_min !== null) params.set('score_min', String(score_min));
    if (score_max !== null) params.set('score_max', String(score_max));

    const response = await fetch(`/api/trust/interactions?${params.toString()}`, { headers: trustHeaders() });
    if (!response.ok) throw new Error(`Trust interactions API error (${response.status})`);
    const pageData = await response.json();

    if ((pageData.total || 0) > 0 && pageData.items.length === 0 && trustState.page > 0) {
        trustState.page = Math.max(0, trustState.page - 1);
        return refreshTrustInteractions();
    }

    renderInteractionRows(pageData);
    if (statusLine) {
        statusLine.textContent = 'Trust metrics loaded.';
    }
}

async function loadTrustSection() {
    if (!trustSectionLoaded) {
        renderTrustShell();
        bindTrustEvents();
        switchTrustPane(trustState.activePane || 'overview');
        trustSectionLoaded = true;
    }
    if (trustSectionLoading) return;

    const statusLine = document.getElementById('trustStatusLine');
    trustSectionLoading = true;
    if (statusLine) statusLine.textContent = 'Loading trust data...';
    try {
        await refreshTrustSummary();
        await refreshTrustInteractions();
        await refreshTrustTimeline();
    } catch (error) {
        console.error('Failed to load trust section:', error);
        if (statusLine) {
            statusLine.textContent = 'Unable to load trust metrics. Verify trust-service/api-gateway and your token.';
        }
    } finally {
        trustSectionLoading = false;
    }
}

function destroyAnalyticsCharts() {
    if (analyticsState.charts.campaignScore) {
        analyticsState.charts.campaignScore.destroy();
        analyticsState.charts.campaignScore = null;
    }
    if (analyticsState.charts.campaignRisk) {
        analyticsState.charts.campaignRisk.destroy();
        analyticsState.charts.campaignRisk = null;
    }
}

function renderAnalyticsShell() {
    const section = document.getElementById('section-analytics');
    if (!section) return;
    section.innerHTML = `
        <div class="section-placeholder trust-layer-shell">
            <h3>Analytics - Campaign Intelligence</h3>
            <p id="analyticsStatusLine">Loading analytics...</p>

            <div id="analyticsKpiGrid" class="trust-kpi-grid" style="margin-top:1rem;"></div>

            <div class="trust-card-block">
                <h4>Campaign Performance Curves</h4>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:.8rem;">
                    <div style="min-height:240px;"><canvas id="analyticsCampaignScoreChart"></canvas></div>
                    <div style="min-height:240px;"><canvas id="analyticsCampaignRiskChart"></canvas></div>
                </div>
            </div>

            <div class="trust-card-block">
                <h4>Campaign Table</h4>
                <div class="trust-table-wrap">
                    <table class="trust-table">
                        <thead>
                            <tr>
                                <th>campaign_id</th>
                                <th>total_interactions</th>
                                <th>avg_score</th>
                                <th>high_risk_rate</th>
                                <th>dominant_segment</th>
                                <th>focus</th>
                            </tr>
                        </thead>
                        <tbody id="analyticsCampaignRows"></tbody>
                    </table>
                </div>
            </div>

            <div class="trust-card-block">
                <h4>Selected Campaign Interactions</h4>
                <div style="display:flex;gap:.6rem;flex-wrap:wrap;margin-bottom:.75rem;">
                    <label style="font-size:.82rem;color:var(--text-muted);align-self:center;">Campaign</label>
                    <select id="analyticsCampaignSelect" class="trust-select"><option value="">All campaigns</option></select>
                </div>
                <div class="trust-table-wrap">
                    <table class="trust-table">
                        <thead>
                            <tr>
                                <th>created_at</th>
                                <th>order_id</th>
                                <th>client_name</th>
                                <th>product_name</th>
                                <th>score</th>
                                <th>segment</th>
                                <th>recommended_action</th>
                            </tr>
                        </thead>
                        <tbody id="analyticsInteractionRows"></tbody>
                    </table>
                </div>
            </div>
        </div>
    `;
}

function analyticsFocusLabel(row) {
    const highRisk = Number(row.high_risk_rate || 0);
    const avgScore = Number(row.avg_interaction_score || 0);
    if (highRisk >= 40) return 'Immediate review';
    if (avgScore < 60) return 'Optimize scripts';
    if (avgScore >= 80 && highRisk < 20) return 'Scale traffic';
    return 'Monitor closely';
}

function renderAnalyticsCharts(summary) {
    if (typeof Chart === 'undefined') return;
    const scoreCanvas = document.getElementById('analyticsCampaignScoreChart');
    const riskCanvas = document.getElementById('analyticsCampaignRiskChart');
    if (!scoreCanvas || !riskCanvas) return;

    const campaigns = Array.isArray(summary?.by_campaign) ? summary.by_campaign : [];
    const labels = campaigns.map((r) => r.campaign_id);
    const scores = campaigns.map((r) => Number(r.avg_interaction_score || 0));
    const risks = campaigns.map((r) => Number(r.high_risk_rate || 0));

    destroyAnalyticsCharts();

    analyticsState.charts.campaignScore = new Chart(scoreCanvas.getContext('2d'), {
        type: 'bar',
        data: {
            labels,
            datasets: [
                {
                    label: 'Avg Score',
                    data: scores,
                    backgroundColor: 'rgba(99, 102, 241, 0.45)',
                    borderColor: 'rgba(99, 102, 241, 0.9)',
                    borderWidth: 1,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { labels: { color: '#94a3b8' } } },
            scales: {
                x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(148,163,184,0.12)' } },
                y: { min: 0, max: 100, ticks: { color: '#94a3b8' }, grid: { color: 'rgba(148,163,184,0.12)' } },
            },
        },
    });

    analyticsState.charts.campaignRisk = new Chart(riskCanvas.getContext('2d'), {
        type: 'line',
        data: {
            labels,
            datasets: [
                {
                    label: 'High Risk Rate %',
                    data: risks,
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.18)',
                    fill: true,
                    tension: 0.35,
                    pointRadius: 3,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { labels: { color: '#94a3b8' } } },
            scales: {
                x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(148,163,184,0.12)' } },
                y: { min: 0, max: 100, ticks: { color: '#94a3b8' }, grid: { color: 'rgba(148,163,184,0.12)' } },
            },
        },
    });
}

function renderAnalyticsTable(summary) {
    const rowsEl = document.getElementById('analyticsCampaignRows');
    const selectEl = document.getElementById('analyticsCampaignSelect');
    if (!rowsEl || !selectEl) return;

    const campaigns = Array.isArray(summary?.by_campaign) ? summary.by_campaign : [];
    if (!campaigns.length) {
        rowsEl.innerHTML = `<tr><td colspan="6" style="padding:.55rem;color:var(--text-muted);">No campaign data yet.</td></tr>`;
        selectEl.innerHTML = `<option value="">All campaigns</option>`;
        return;
    }

    rowsEl.innerHTML = campaigns.map((row) => `
        <tr data-analytics-campaign="${escapeHtml(row.campaign_id)}" style="cursor:pointer;">
            <td>${escapeHtml(row.campaign_id)}</td>
            <td>${escapeHtml(row.total_interactions)}</td>
            <td>${escapeHtml(row.avg_interaction_score)}</td>
            <td>${escapeHtml(row.high_risk_rate)}%</td>
            <td>${segmentBadge(row.dominant_segment)}</td>
            <td>${escapeHtml(analyticsFocusLabel(row))}</td>
        </tr>
    `).join('');

    selectEl.innerHTML = `<option value="">All campaigns</option>${campaigns.map((row) => `<option value="${escapeHtml(row.campaign_id)}">${escapeHtml(row.campaign_id)}</option>`).join('')}`;
    selectEl.value = analyticsState.selectedCampaign || '';

    rowsEl.querySelectorAll('tr[data-analytics-campaign]').forEach((tr) => {
        tr.addEventListener('click', () => {
            analyticsState.selectedCampaign = tr.dataset.analyticsCampaign || '';
            if (selectEl) selectEl.value = analyticsState.selectedCampaign;
            loadAnalyticsInteractions();
        });
    });
}

async function loadAnalyticsInteractions() {
    const rowsEl = document.getElementById('analyticsInteractionRows');
    if (!rowsEl) return;

    const params = new URLSearchParams();
    params.set('limit', '25');
    params.set('offset', '0');
    params.set('sort', 'date_desc');
    if (analyticsState.selectedCampaign) params.set('campaign_id', analyticsState.selectedCampaign);

    const response = await fetch(`/api/trust/interactions?${params.toString()}`, { headers: trustHeaders() });
    if (!response.ok) {
        rowsEl.innerHTML = `<tr><td colspan="7" style="padding:.55rem;color:#f87171;">Unable to load interactions.</td></tr>`;
        return;
    }

    const pageData = await response.json();
    const items = Array.isArray(pageData?.items) ? pageData.items : [];
    if (!items.length) {
        rowsEl.innerHTML = `<tr><td colspan="7" style="padding:.55rem;color:var(--text-muted);">No interactions for this campaign.</td></tr>`;
        return;
    }

    rowsEl.innerHTML = items.map((row) => `
        <tr>
            <td>${escapeHtml(formatDateTime(row.created_at))}</td>
            <td>${escapeHtml(row.order_id)}</td>
            <td>${escapeHtml(row.client_name || '-')}</td>
            <td>${escapeHtml(row.product_name || '-')}</td>
            <td>${escapeHtml(row.interaction_score)}</td>
            <td>${segmentBadge(row.segment)}</td>
            <td>${escapeHtml(row.recommended_action)}</td>
        </tr>
    `).join('');
}

async function loadAnalyticsSection() {
    if (analyticsSectionLoading) return;
    if (!analyticsSectionLoaded) {
        renderAnalyticsShell();
        analyticsSectionLoaded = true;
    }

    const statusLine = document.getElementById('analyticsStatusLine');
    const kpiGrid = document.getElementById('analyticsKpiGrid');
    const campaignSelect = document.getElementById('analyticsCampaignSelect');
    analyticsSectionLoading = true;
    if (statusLine) statusLine.textContent = 'Loading analytics...';

    try {
        const summaryResp = await fetch('/api/trust/metrics/summary', { headers: trustHeaders() });
        if (!summaryResp.ok) throw new Error(`Analytics API error (${summaryResp.status})`);
        const summary = await summaryResp.json();

        const campaigns = Array.isArray(summary.by_campaign) ? summary.by_campaign : [];
        const bestCampaign = campaigns.length ? campaigns[0] : null;
        const riskyCampaigns = campaigns.filter((r) => Number(r.high_risk_rate || 0) >= 40).length;

        if (kpiGrid) {
            kpiGrid.innerHTML = [
                metricCard('Total campaigns', campaigns.length),
                metricCard('Best campaign score', bestCampaign ? bestCampaign.avg_interaction_score : 0),
                metricCard('Risky campaigns', riskyCampaigns),
                metricCard('Trust global avg', summary.avg_interaction_score ?? 0),
                metricCard('HIGH_RISK total', summary.high_risk_count ?? 0),
                metricCard('Last trust update', formatDateTime(summary.last_interaction_at)),
            ].join('');
        }

        renderAnalyticsCharts(summary);
        renderAnalyticsTable(summary);

        if (campaignSelect && !campaignSelect.dataset.bound) {
            campaignSelect.addEventListener('change', () => {
                analyticsState.selectedCampaign = campaignSelect.value || '';
                loadAnalyticsInteractions();
            });
            campaignSelect.dataset.bound = '1';
        }
        await loadAnalyticsInteractions();

        if (statusLine) statusLine.textContent = 'Analytics loaded with real trust data.';
    } catch (error) {
        console.error('Failed to load analytics section:', error);
        if (statusLine) statusLine.textContent = 'Unable to load analytics.';
    } finally {
        analyticsSectionLoading = false;
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
    if (document.getElementById('ordersChange')) {
        document.getElementById('ordersChange').textContent = `${data.orders_today || 0} today`;
    }
    if (document.getElementById('confirmedChange')) {
        const total = Number(data.total_orders || 0);
        const confirmed = Number(data.confirmed_orders || 0);
        const rate = total > 0 ? ((confirmed / total) * 100).toFixed(1) : '0.0';
        document.getElementById('confirmedChange').textContent = `${rate}% confirm`;
    }
    if (document.getElementById('pendingChange')) {
        document.getElementById('pendingChange').textContent = `${data.pending_orders || 0} pending`;
    }
    if (document.getElementById('revenueChange')) {
        document.getElementById('revenueChange').textContent = `${data.high_risk_orders || 0} risk alerts`;
    }
}

async function loadDashboardCharts() {
    const token = getAuthToken();
    if (!token || typeof Chart === 'undefined') return;

    try {
        const [revenueResp, statsResp] = await Promise.all([
            fetch('/api/dashboard/revenue-chart?days=7', { headers: { Authorization: `Bearer ${token}` } }),
            fetch('/api/dashboard/stats', { headers: { Authorization: `Bearer ${token}` } }),
        ]);
        if (!revenueResp.ok || !statsResp.ok) return;

        const revenue = await revenueResp.json();
        const stats = await statsResp.json();

        const revenueCanvas = document.getElementById('revenueChart');
        if (revenueCanvas) {
            if (dashboardRevenueChart) dashboardRevenueChart.destroy();
            dashboardRevenueChart = new Chart(revenueCanvas.getContext('2d'), {
                type: 'line',
                data: {
                    labels: revenue.labels || [],
                    datasets: [
                        {
                            label: 'Revenue',
                            data: revenue.data || [],
                            borderColor: '#3b82f6',
                            backgroundColor: 'rgba(59,130,246,.16)',
                            fill: true,
                            tension: 0.35,
                            pointRadius: 3,
                        },
                    ],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { labels: { color: '#94a3b8' } } },
                    scales: {
                        x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(148,163,184,.12)' } },
                        y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(148,163,184,.12)' } },
                    },
                },
            });
        }

        const orderStatusCanvas = document.getElementById('orderStatusChart');
        if (orderStatusCanvas) {
            if (dashboardOrderStatusChart) dashboardOrderStatusChart.destroy();
            dashboardOrderStatusChart = new Chart(orderStatusCanvas.getContext('2d'), {
                type: 'doughnut',
                data: {
                    labels: ['Confirmed', 'Pending', 'Rejected'],
                    datasets: [
                        {
                            data: [
                                Number(stats.confirmed_orders || 0),
                                Number(stats.pending_orders || 0),
                                Number(stats.rejected_orders || 0),
                            ],
                            backgroundColor: ['#10b981', '#f59e0b', '#ef4444'],
                            borderWidth: 0,
                        },
                    ],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { labels: { color: '#94a3b8' } } },
                },
            });
        }
    } catch (error) {
        console.error('Error loading dashboard charts:', error);
    }
}

async function loadDashboardTrustLinkage() {
    const token = getAuthToken();
    if (!token) return;
    try {
        const response = await fetch('/api/trust/metrics/summary', {
            headers: { Authorization: `Bearer ${token}` },
        });
        if (!response.ok) return;
        const trust = await response.json();
        if (document.getElementById('pendingChange')) {
            document.getElementById('pendingChange').textContent = `${trust.high_risk_count || 0} HIGH_RISK`;
        }
        if (document.getElementById('revenueChange')) {
            document.getElementById('revenueChange').textContent = `Trust avg ${trust.avg_interaction_score || 0}`;
        }
    } catch (error) {
        console.error('Error loading trust linkage:', error);
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





