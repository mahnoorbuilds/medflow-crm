/* ═══════════════════════════════════════════════
   MedFlow CRM — Frontend Logic
   ═══════════════════════════════════════════════ */

const API = window.location.origin;

// ── Helpers ──────────────────────────────────
function formatTime(isoStr) {
    const d = new Date(isoStr);
    return d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true });
}

function formatDate(isoStr) {
    const d = new Date(isoStr);
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function formatDateTime(isoStr) {
    return formatDate(isoStr) + ' at ' + formatTime(isoStr);
}

function todayISO() {
    const d = new Date();
    return d.getFullYear() + '-' +
        String(d.getMonth() + 1).padStart(2, '0') + '-' +
        String(d.getDate()).padStart(2, '0');
}

function tomorrowISO() {
    const d = new Date();
    d.setDate(d.getDate() + 1);
    return d.getFullYear() + '-' +
        String(d.getMonth() + 1).padStart(2, '0') + '-' +
        String(d.getDate()).padStart(2, '0');
}

// ── Toast Notifications ─────────────────────
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    const icons = {
        success: '✓',
        error: '✕',
        info: 'ℹ'
    };

    toast.innerHTML = `<span style="font-size:1.1rem">${icons[type] || 'ℹ'}</span> ${message}`;
    container.appendChild(toast);

    setTimeout(() => {
        if (toast.parentNode) toast.remove();
    }, 4000);
}

// ── API Calls ───────────────────────────────
async function apiGet(path) {
    const res = await fetch(`${API}${path}`);
    if (!res.ok) {
        const text = await res.text();
        throw new Error(text || res.statusText);
    }
    return res.json();
}

async function apiPost(path, body) {
    const res = await fetch(`${API}${path}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    });
    if (!res.ok) {
        const text = await res.text();
        throw new Error(text || res.statusText);
    }
    return res.json();
}

// ── Load Stats ──────────────────────────────
async function loadStats() {
    try {
        const stats = await apiGet('/api/stats');
        document.getElementById('statTotal').textContent = stats.total;
        document.getElementById('statToday').textContent = stats.today;
        document.getElementById('statUpcoming').textContent = stats.upcoming;
        document.getElementById('statCanceled').textContent = stats.canceled;

        // Animate numbers
        document.querySelectorAll('.stat-value').forEach(el => {
            el.style.animation = 'none';
            el.offsetHeight; // trigger reflow
            el.style.animation = 'fadeIn 0.4s ease';
        });
    } catch (err) {
        console.error('Stats error:', err);
    }
}

// ── Load Appointments for Dashboard ─────────
async function loadDashboardAppointments(date) {
    const tbody = document.getElementById('dashboardTableBody');
    const empty = document.getElementById('dashboardEmpty');
    const table = document.getElementById('dashboardTable');

    tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;padding:20px"><div class="spinner"></div></td></tr>';

    try {
        const data = await apiGet(`/api/appointments?date=${date}`);
        tbody.innerHTML = '';

        if (!data.length) {
            table.style.display = 'none';
            empty.style.display = 'flex';
            return;
        }

        table.style.display = '';
        empty.style.display = 'none';

        data.forEach(appt => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><strong>${escapeHtml(appt.patient_name)}</strong></td>
                <td>${formatTime(appt.start_time)}</td>
                <td>${escapeHtml(appt.reason || '—')}</td>
                <td><span class="badge ${appt.canceled ? 'badge-canceled' : 'badge-active'}">${appt.canceled ? 'Canceled' : 'Active'}</span></td>
                <td>${!appt.canceled ? `<button class="btn-cancel-action" onclick="cancelSingle('${escapeHtml(appt.patient_name)}', '${date}')">Cancel</button>` : '—'}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;padding:20px;color:var(--accent-red)">Error loading appointments</td></tr>`;
        console.error(err);
    }
}

// ── Load All Appointments ───────────────────
async function loadAllAppointments(date, status) {
    const tbody = document.getElementById('appointmentsTableBody');
    const empty = document.getElementById('appointmentsEmpty');

    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:20px"><div class="spinner"></div></td></tr>';

    try {
        let url = '/api/appointments';
        const params = [];
        if (date) params.push(`date=${date}`);
        if (status && status !== 'all') params.push(`status=${status}`);
        if (params.length) url += '?' + params.join('&');

        const data = await apiGet(url);
        tbody.innerHTML = '';

        if (!data.length) {
            empty.style.display = 'flex';
            return;
        }

        empty.style.display = 'none';

        data.forEach(appt => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>#${appt.id}</td>
                <td><strong>${escapeHtml(appt.patient_name)}</strong></td>
                <td>${formatDateTime(appt.start_time)}</td>
                <td>${escapeHtml(appt.reason || '—')}</td>
                <td><span class="badge ${appt.canceled ? 'badge-canceled' : 'badge-active'}">${appt.canceled ? 'Canceled' : 'Active'}</span></td>
                <td>${formatDate(appt.created_at)}</td>
                <td>${!appt.canceled ? `<button class="btn-cancel-action" onclick="cancelSingle('${escapeHtml(appt.patient_name)}', '${appt.start_time.split('T')[0]}')">Cancel</button>` : '—'}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;padding:20px;color:var(--accent-red)">Error loading</td></tr>`;
    }
}

// ── Schedule Appointment ────────────────────
async function scheduleAppointment(name, reason, date, time) {
    const startTime = `${date}T${time}:00`;
    const data = await apiPost('/schedule_appointment/', {
        patient_name: name,
        reason: reason,
        start_time: startTime,
    });
    return data;
}

// ── Cancel Appointment ──────────────────────
async function cancelSingle(patientName, date) {
    if (!confirm(`Cancel all appointments for "${patientName}" on ${date}?`)) return;

    try {
        await apiPost('/cancel_appointment/', {
            patient_name: patientName,
            date: date,
        });
        showToast(`Appointments canceled for ${patientName}`, 'success');
        refreshCurrentView();
    } catch (err) {
        showToast('Cancel failed: ' + err.message, 'error');
    }
}

// ── Escape HTML ─────────────────────────────
function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// ── Navigation ──────────────────────────────
const navItems = document.querySelectorAll('.nav-item');
const pages = document.querySelectorAll('.page');
const pageTitle = document.getElementById('pageTitle');

const pageTitles = {
    dashboard: 'Dashboard',
    appointments: 'Appointments',
    schedule: 'Schedule & Manage',
};

function navigateTo(pageName) {
    navItems.forEach(n => n.classList.remove('active'));
    pages.forEach(p => p.classList.remove('active'));

    const navEl = document.querySelector(`[data-page="${pageName}"]`);
    const pageEl = document.getElementById(`page-${pageName}`);

    if (navEl) navEl.classList.add('active');
    if (pageEl) pageEl.classList.add('active');

    pageTitle.textContent = pageTitles[pageName] || pageName;

    // Load data for the page
    if (pageName === 'dashboard') {
        loadStats();
        loadDashboardAppointments(document.getElementById('dashboardDate').value);
    } else if (pageName === 'appointments') {
        const date = document.getElementById('filterDate').value;
        const status = document.getElementById('filterStatus').value;
        loadAllAppointments(date, status);
    }

    // Close mobile sidebar
    document.getElementById('sidebar').classList.remove('open');
}

navItems.forEach(item => {
    item.addEventListener('click', (e) => {
        e.preventDefault();
        navigateTo(item.dataset.page);
    });
});

// ── Refresh current view ────────────────────
function refreshCurrentView() {
    const active = document.querySelector('.nav-item.active');
    if (active) navigateTo(active.dataset.page);
}

// ── Date Navigation ─────────────────────────
const dashboardDate = document.getElementById('dashboardDate');
dashboardDate.value = todayISO();

dashboardDate.addEventListener('change', () => {
    loadDashboardAppointments(dashboardDate.value);
});

document.getElementById('prevDay').addEventListener('click', () => {
    const d = new Date(dashboardDate.value);
    d.setDate(d.getDate() - 1);
    dashboardDate.value = d.toISOString().split('T')[0];
    loadDashboardAppointments(dashboardDate.value);
});

document.getElementById('nextDay').addEventListener('click', () => {
    const d = new Date(dashboardDate.value);
    d.setDate(d.getDate() + 1);
    dashboardDate.value = d.toISOString().split('T')[0];
    loadDashboardAppointments(dashboardDate.value);
});

// ── Appointments Page Filters ───────────────
document.getElementById('filterDate').addEventListener('change', () => {
    loadAllAppointments(
        document.getElementById('filterDate').value,
        document.getElementById('filterStatus').value
    );
});

document.getElementById('filterStatus').addEventListener('change', () => {
    loadAllAppointments(
        document.getElementById('filterDate').value,
        document.getElementById('filterStatus').value
    );
});

// ── Schedule Modal ──────────────────────────
const scheduleModal = document.getElementById('scheduleModal');

function openScheduleModal() {
    document.getElementById('modalDate').value = tomorrowISO();
    document.getElementById('modalTime').value = '09:00';
    scheduleModal.classList.add('open');
}

function closeScheduleModal() {
    scheduleModal.classList.remove('open');
}

document.getElementById('newAppointmentBtn').addEventListener('click', openScheduleModal);
document.getElementById('closeModal').addEventListener('click', closeScheduleModal);

scheduleModal.addEventListener('click', (e) => {
    if (e.target === scheduleModal) closeScheduleModal();
});

// Modal form submit
document.getElementById('scheduleFormModal').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = e.target.querySelector('button[type="submit"]');
    const origText = btn.innerHTML;
    btn.innerHTML = '<div class="spinner"></div> Scheduling...';
    btn.disabled = true;

    try {
        await scheduleAppointment(
            document.getElementById('modalPatientName').value.trim(),
            document.getElementById('modalReason').value.trim(),
            document.getElementById('modalDate').value,
            document.getElementById('modalTime').value,
        );
        showToast('Appointment scheduled successfully!', 'success');
        closeScheduleModal();
        e.target.reset();
        refreshCurrentView();
    } catch (err) {
        showToast('Failed to schedule: ' + err.message, 'error');
    } finally {
        btn.innerHTML = origText;
        btn.disabled = false;
    }
});

// ── Schedule Page Form ──────────────────────
document.getElementById('pgDate').value = tomorrowISO();
document.getElementById('pgTime').value = '09:00';
document.getElementById('cancelDate').value = todayISO();

document.getElementById('scheduleFormPage').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = e.target.querySelector('button[type="submit"]');
    const origText = btn.innerHTML;
    btn.innerHTML = '<div class="spinner"></div> Scheduling...';
    btn.disabled = true;

    try {
        await scheduleAppointment(
            document.getElementById('pgPatientName').value.trim(),
            document.getElementById('pgReason').value.trim(),
            document.getElementById('pgDate').value,
            document.getElementById('pgTime').value,
        );
        showToast('Appointment scheduled successfully!', 'success');
        e.target.reset();
        document.getElementById('pgDate').value = tomorrowISO();
        document.getElementById('pgTime').value = '09:00';
        loadStats();
    } catch (err) {
        showToast('Failed to schedule: ' + err.message, 'error');
    } finally {
        btn.innerHTML = origText;
        btn.disabled = false;
    }
});

// ── Cancel Form ─────────────────────────────
document.getElementById('cancelForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('cancelName').value.trim();
    const date = document.getElementById('cancelDate').value;

    if (!name || !date) return showToast('Please fill all fields', 'error');

    const btn = e.target.querySelector('button[type="submit"]');
    const origText = btn.innerHTML;
    btn.innerHTML = '<div class="spinner"></div> Canceling...';
    btn.disabled = true;

    try {
        const data = await apiPost('/cancel_appointment/', {
            patient_name: name,
            date: date,
        });
        if (data.canceled_count) {
            showToast(`${data.canceled_count} appointment(s) canceled`, 'success');
        } else {
            showToast('No matching appointments found', 'info');
        }
        e.target.reset();
        document.getElementById('cancelDate').value = todayISO();
        loadStats();
    } catch (err) {
        showToast('Cancel failed: ' + err.message, 'error');
    } finally {
        btn.innerHTML = origText;
        btn.disabled = false;
    }
});

// ── Search ──────────────────────────────────
let searchTimeout;
document.getElementById('searchInput').addEventListener('input', (e) => {
    clearTimeout(searchTimeout);
    const query = e.target.value.trim();

    searchTimeout = setTimeout(async () => {
        if (query.length < 2) return;

        try {
            const data = await apiGet(`/api/appointments/search?name=${encodeURIComponent(query)}`);
            // Switch to appointments page and show results
            navigateTo('appointments');

            const tbody = document.getElementById('appointmentsTableBody');
            const empty = document.getElementById('appointmentsEmpty');
            tbody.innerHTML = '';

            if (!data.length) {
                empty.style.display = 'flex';
                return;
            }

            empty.style.display = 'none';
            data.forEach(appt => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>#${appt.id}</td>
                    <td><strong>${escapeHtml(appt.patient_name)}</strong></td>
                    <td>${formatDateTime(appt.start_time)}</td>
                    <td>${escapeHtml(appt.reason || '—')}</td>
                    <td><span class="badge ${appt.canceled ? 'badge-canceled' : 'badge-active'}">${appt.canceled ? 'Canceled' : 'Active'}</span></td>
                    <td>${formatDate(appt.created_at)}</td>
                    <td>${!appt.canceled ? `<button class="btn-cancel-action" onclick="cancelSingle('${escapeHtml(appt.patient_name)}', '${appt.start_time.split('T')[0]}')">Cancel</button>` : '—'}</td>
                `;
                tbody.appendChild(tr);
            });
        } catch (err) {
            console.error('Search error:', err);
        }
    }, 300);
});

// ── Mobile Menu ─────────────────────────────
document.getElementById('mobileMenuBtn').addEventListener('click', () => {
    document.getElementById('sidebar').classList.toggle('open');
});

// ── Sidebar Toggle ──────────────────────────
document.getElementById('sidebarToggle').addEventListener('click', () => {
    document.getElementById('sidebar').classList.toggle('open');
});

// ── Initial Load ────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    loadStats();
    loadDashboardAppointments(todayISO());
});
