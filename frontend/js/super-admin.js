function getToken() {
  return localStorage.getItem('access_token') || localStorage.getItem('token');
}

function logoutNow() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('token');
  localStorage.removeItem('user_id');
  window.location.replace('login.html');
}

function decodeJwtPayload(token) {
  try {
    const payload = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
    const json = atob(payload);
    return JSON.parse(json);
  } catch (e) {
    return null;
  }
}

function ensureAdminAccess() {
  const token = getToken();
  if (!token) {
    window.location.replace('login.html');
    return null;
  }

  const payload = decodeJwtPayload(token);
  const role = (payload?.role || '').toLowerCase();
  if (!['admin', 'super_admin', 'founder'].includes(role)) {
    window.location.replace('dashboard.html');
    return null;
  }

  return token;
}

function renderOverview(data) {
  const totals = data?.totals || {};
  document.getElementById('mUsers').textContent = totals.users ?? 0;
  document.getElementById('mBoutiques').textContent = totals.boutiques ?? 0;
  document.getElementById('mCustomers').textContent = totals.customers ?? 0;
  document.getElementById('mOrders').textContent = totals.orders ?? 0;
  document.getElementById('mPayments').textContent = totals.payments ?? 0;
  document.getElementById('mRevenue').textContent = `$${Number(totals.revenue || 0).toFixed(2)}`;

  const usersBody = document.getElementById('recentUsersBody');
  const users = Array.isArray(data?.recent_users) ? data.recent_users : [];
  usersBody.innerHTML = users.length
    ? users.map((u) => `<tr><td>${u.id}</td><td>${u.full_name || '-'}</td><td>${u.email || '-'}</td><td>${u.role || '-'}</td></tr>`).join('')
    : '<tr><td colspan="4" class="muted">No users.</td></tr>';

  const paymentsBody = document.getElementById('recentPaymentsBody');
  const payments = Array.isArray(data?.recent_payments) ? data.recent_payments : [];
  paymentsBody.innerHTML = payments.length
    ? payments.map((p) => `<tr><td>${p.id}</td><td>${p.user_id}</td><td>${p.plan || '-'}</td><td>$${Number(p.amount || 0).toFixed(2)}</td></tr>`).join('')
    : '<tr><td colspan="4" class="muted">No payments.</td></tr>';
}

async function adminFetch(path, options = {}) {
  const token = ensureAdminAccess();
  if (!token) throw new Error('No admin token');
  const response = await fetch(`http://localhost:8000${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      ...(options.headers || {}),
    },
  });
  if (response.status === 401) {
    logoutNow();
    throw new Error('Unauthorized');
  }
  if (response.status === 403) {
    window.location.replace('dashboard.html');
    throw new Error('Forbidden');
  }
  return response;
}

function renderUsersCrud(users) {
  const tbody = document.getElementById('usersCrudBody');
  if (!tbody) return;
  if (!Array.isArray(users) || !users.length) {
    tbody.innerHTML = '<tr><td colspan="5" class="muted">No users.</td></tr>';
    return;
  }
  tbody.innerHTML = users.map((u) => `
    <tr>
      <td>${u.id}</td>
      <td>${u.full_name || '-'}</td>
      <td>${u.email || '-'}</td>
      <td>${u.role || '-'}</td>
      <td>
        <button class="action-btn" data-action="edit" data-id="${u.id}">Edit</button>
        <button class="action-btn" data-action="delete" data-id="${u.id}">Delete</button>
      </td>
    </tr>
  `).join('');
}

async function loadUsersCrud() {
  const res = await adminFetch('/admin/users');
  if (!res.ok) throw new Error('Failed to load users');
  const users = await res.json();
  renderUsersCrud(users);
}

async function createUserFromForm() {
  const full_name = document.getElementById('newUserName')?.value?.trim() || null;
  const email = document.getElementById('newUserEmail')?.value?.trim();
  const password = document.getElementById('newUserPassword')?.value?.trim();
  const role = document.getElementById('newUserRole')?.value || 'user';
  if (!email || !password) {
    alert('Email and password are required.');
    return;
  }

  const res = await adminFetch('/admin/users', {
    method: 'POST',
    body: JSON.stringify({ full_name, email, password, role }),
  });
  if (!res.ok) {
    const err = await res.text();
    alert(`Create failed: ${err}`);
    return;
  }
  document.getElementById('newUserName').value = '';
  document.getElementById('newUserEmail').value = '';
  document.getElementById('newUserPassword').value = '';
  document.getElementById('newUserRole').value = 'user';
  await loadAdminOverview();
  await loadUsersCrud();
}

async function editUser(userId) {
  const role = prompt('New role (user/admin/founder):');
  if (!role) return;
  const fullName = prompt('New full name (leave empty to keep):');
  const payload = { role: role.trim().toLowerCase() };
  if (fullName !== null && fullName.trim() !== '') {
    payload.full_name = fullName.trim();
  }
  const res = await adminFetch(`/admin/users/${userId}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.text();
    alert(`Update failed: ${err}`);
    return;
  }
  await loadAdminOverview();
  await loadUsersCrud();
}

async function deleteUser(userId) {
  const ok = confirm(`Delete user #${userId}?`);
  if (!ok) return;
  const res = await adminFetch(`/admin/users/${userId}`, { method: 'DELETE' });
  if (!res.ok) {
    const err = await res.text();
    alert(`Delete failed: ${err}`);
    return;
  }
  await loadAdminOverview();
  await loadUsersCrud();
}

async function loadAdminOverview() {
  const token = ensureAdminAccess();
  if (!token) return;

  const res = await fetch('http://localhost:8000/admin/overview', {
    headers: { Authorization: `Bearer ${token}` },
  });

  if (res.status === 401) {
    logoutNow();
    return;
  }

  if (res.status === 403) {
    window.location.replace('dashboard.html');
    return;
  }

  if (!res.ok) {
    throw new Error('Failed to load admin overview');
  }

  const data = await res.json();
  renderOverview(data);
}

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('logoutAdmin')?.addEventListener('click', logoutNow);
  document.getElementById('refreshAdmin')?.addEventListener('click', () => {
    loadAdminOverview().catch(() => {});
  });
  document.getElementById('goUserDashboard')?.addEventListener('click', () => {
    window.location.href = 'dashboard.html';
  });
  document.getElementById('createUserBtn')?.addEventListener('click', () => {
    createUserFromForm().catch(() => {
      alert('Create user failed.');
    });
  });
  document.getElementById('usersCrudBody')?.addEventListener('click', (e) => {
    const target = e.target;
    if (!(target instanceof HTMLElement)) return;
    const action = target.getAttribute('data-action');
    const id = Number(target.getAttribute('data-id'));
    if (!id || !action) return;
    if (action === 'edit') {
      editUser(id).catch(() => {
        alert('Update failed.');
      });
    }
    if (action === 'delete') {
      deleteUser(id).catch(() => {
        alert('Delete failed.');
      });
    }
  });

  loadAdminOverview().catch(() => {
    alert('Unable to load admin data.');
  });
  loadUsersCrud().catch(() => {
    const body = document.getElementById('usersCrudBody');
    if (body) body.innerHTML = '<tr><td colspan="5" class="muted">Failed to load users.</td></tr>';
  });
});
