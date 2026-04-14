// ── shared.js ────────────────────────────────────────────────────────────────
const API = (typeof BACKEND_URL !== 'undefined' ? BACKEND_URL : 'http://localhost:8000') + '/api';

function getToken()  { return localStorage.getItem('token'); }
function isAdmin()   { return localStorage.getItem('isAdmin') === 'true'; }
function esc(s)      { return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }

function guardAdmin() {
  if (!getToken()) { window.location.href = 'login.html'; return false; }
  if (!isAdmin())  { window.location.href = 'student.html'; return false; }
  return true;
}
function guardStudent() {
  if (!getToken()) { window.location.href = 'login.html'; return false; }
  if (isAdmin())   { window.location.href = 'dashboard.html'; return false; }
  return true;
}

// ── API helpers ───────────────────────────────────────────────────────────────
async function apiFetch(path, options = {}) {
  const res = await fetch(`${API}${path}`, {
    ...options,
    headers: { 'Authorization': `Token ${getToken()}`, 'Content-Type': 'application/json', ...(options.headers||{}) }
  });
  if (res.status === 401) { localStorage.clear(); window.location.href = 'login.html'; }
  return res;
}
async function apiGet(path) {
  const r = await apiFetch(path);
  if (!r.ok) return [];
  return r.json();
}
async function apiPost(path, body) {
  const r = await apiFetch(path, { method:'POST', body: JSON.stringify(body) });
  let data = {};
  try { data = await r.json(); } catch {}
  return { ok: r.ok, status: r.status, data };
}
async function apiPatch(path, body) {
  const r = await apiFetch(path, { method:'PATCH', body: JSON.stringify(body) });
  let data = {};
  try { data = await r.json(); } catch {}
  return { ok: r.ok, status: r.status, data };
}
async function apiDelete(path) { return apiFetch(path, { method:'DELETE' }); }

// ── UI helpers ────────────────────────────────────────────────────────────────
function badge(text) {
  const map = {
    present:'background:#e6fffa;color:#2c7a7b', absent:'background:#fff5f5;color:#c53030',
    login:'background:#ebf8ff;color:#2b6cb0',   logout:'background:#faf5ff;color:#6b46c1',
    sent:'background:#e6fffa;color:#2c7a7b',    failed:'background:#fff5f5;color:#c53030',
    pending:'background:#fffbeb;color:#b7791f', general:'background:#f0f4ff;color:#4361ee'
  };
  const s = map[text?.toLowerCase()] || 'background:#f7fafc;color:#4a5568';
  return `<span style="${s};font-size:11px;font-weight:600;padding:3px 8px;border-radius:20px;text-transform:capitalize;display:inline-block">${esc(text)||'—'}</span>`;
}

function fmtTime(dt) {
  if (!dt) return '—';
  return new Date(dt).toLocaleTimeString('en-IN', { hour:'2-digit', minute:'2-digit' });
}
function fmtDate(dt) {
  if (!dt) return '—';
  return new Date(dt).toLocaleString('en-IN', { day:'2-digit', month:'short', hour:'2-digit', minute:'2-digit' });
}

function showToast(msg, type='success') {
  let t = document.getElementById('_toast');
  if (!t) {
    t = document.createElement('div');
    t.id = '_toast';
    t.style.cssText = 'position:fixed;bottom:24px;right:24px;padding:12px 20px;border-radius:10px;font-size:14px;font-weight:500;z-index:9999;transition:opacity .3s;box-shadow:0 4px 12px rgba(0,0,0,.15);pointer-events:none';
    document.body.appendChild(t);
  }
  t.textContent = msg;
  t.style.background = type === 'success' ? '#2ec4b6' : '#e63946';
  t.style.color = '#fff';
  t.style.opacity = '1';
  clearTimeout(t._tmr);
  t._tmr = setTimeout(() => { t.style.opacity = '0'; }, 3000);
}

// ── Global CSS injected once ───────────────────────────────────────────────────
(function injectGlobalCSS() {
  if (document.getElementById('_globalCSS')) return;
  const s = document.createElement('style');
  s.id = '_globalCSS';
  s.textContent = `
    *{box-sizing:border-box;margin:0;padding:0}
    body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:#1a1a2e;background:#f0f2f5}
    a{text-decoration:none;color:inherit}
    input,select,textarea,button{font-family:inherit}
    .btn-primary{background:#1a1a2e;color:#fff;border:none;padding:9px 18px;border-radius:8px;font-size:14px;font-weight:500;cursor:pointer}
    .btn-primary:hover{background:#16213e}
    .btn-primary:disabled{background:#a0aec0;cursor:not-allowed}
    .btn-danger{background:#fff5f5;color:#c53030;border:1px solid #fed7d7;padding:4px 12px;border-radius:6px;font-size:12px;cursor:pointer}
    .btn-blue{background:#ebf8ff;color:#2b6cb0;border:none;padding:5px 12px;border-radius:6px;font-size:12px;cursor:pointer;font-weight:500}
    .btn-green{background:#f0fff4;color:#276749;border:none;padding:5px 12px;border-radius:6px;font-size:12px;cursor:pointer;font-weight:500}
    .btn-ghost-del{background:none;border:none;color:#adb5bd;font-size:15px;cursor:pointer;line-height:1;padding:0 2px}
    .btn-ghost-del:hover{color:#e63946}
    .inp{width:100%;padding:9px 12px;border:1px solid #dee2e6;border-radius:8px;font-size:14px;outline:none;background:#fff}
    .inp:focus{border-color:#4361ee}
    .page-header{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:24px}
    .page-title{font-size:22px;font-weight:700;margin-bottom:3px}
    .page-sub{font-size:14px;color:#6c757d}
    .panel{background:#fff;border-radius:10px;box-shadow:0 1px 3px rgba(0,0,0,.08);overflow:hidden}
    .panel-head{padding:14px 20px;border-bottom:1px solid #e9ecef;font-weight:600;font-size:15px}
    .stat-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:16px;margin-bottom:24px}
    .stat-card{background:#fff;border-radius:10px;padding:20px 22px;box-shadow:0 1px 3px rgba(0,0,0,.08)}
    .stat-label{font-size:11px;color:#6c757d;font-weight:600;text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px}
    .stat-value{font-size:28px;font-weight:700;color:#1a1a2e}
    .stat-sub{font-size:12px;color:#6c757d;margin-top:4px}
    .data-table{width:100%;border-collapse:collapse;font-size:14px}
    .data-table th{padding:11px 16px;text-align:left;font-size:11px;font-weight:600;color:#6c757d;text-transform:uppercase;letter-spacing:.5px;background:#f8f9fa;border-bottom:1px solid #e9ecef}
    .data-table td{padding:12px 16px;border-bottom:1px solid #f0f2f5;color:#495057}
    .data-table tr:hover td{background:#f8f9fa}
    .data-table tr:last-child td{border-bottom:none}
    .scroll-list{max-height:360px;overflow-y:auto}
    .list-item{display:flex;justify-content:space-between;align-items:center;padding:10px 18px;border-bottom:1px solid #f0f2f5}
    .list-item:last-child{border-bottom:none}
    .empty-state{padding:40px;text-align:center;color:#6c757d;font-size:14px}
    .pbar-wrap{height:6px;background:#e9ecef;border-radius:3px}
    .pbar{height:100%;border-radius:3px;background:#4361ee}
    .chip{display:inline-flex;align-items:center;gap:5px;padding:4px 10px;border-radius:20px;font-size:12px;font-weight:500}
    .chip-done{background:#e6fffa;color:#2c7a7b}
    .chip-todo{background:#f0f2f5;color:#adb5bd}
    .chip-topic{background:#f0f4ff;color:#4361ee}
    .g2{display:grid;grid-template-columns:1fr 1fr;gap:0 16px}
  `;
  document.head.appendChild(s);
})();

// ── Sidebar layout ────────────────────────────────────────────────────────────
const ADMIN_NAV = [
  { href:'dashboard.html', icon:'⊞', label:'Dashboard'  },
  { href:'students.html',  icon:'👥', label:'Students'   },
  { href:'attendance.html',icon:'📅', label:'Attendance' },
  { href:'progress.html',  icon:'📈', label:'Progress'   },
  { href:'groups.html',    icon:'🗂',  label:'Groups'     },
  { href:'courses.html',   icon:'📚', label:'Courses'    },
  { href:'reports.html',   icon:'📄', label:'Reports'    },
];

function renderAdminLayout(contentHtml) {
  const cur = location.pathname.split('/').pop();
  const nav = ADMIN_NAV.map(n => {
    const active = cur === n.href;
    return `<a href="${n.href}" style="
      display:flex;align-items:center;gap:10px;padding:10px;border-radius:8px;margin-bottom:2px;
      color:${active ? '#fff' : 'rgba(255,255,255,0.65)'};
      background:${active ? 'rgba(255,255,255,0.15)' : 'transparent'};
      font-weight:${active ? 600 : 400};font-size:14px;text-decoration:none;transition:background .15s">
      <span style="font-size:16px;width:20px;text-align:center;flex-shrink:0">${n.icon}</span>
      <span>${n.label}</span>
    </a>`;
  }).join('');

  document.body.innerHTML = `
    <div style="display:flex;min-height:100vh">
      <aside style="width:220px;background:#1a1a2e;color:#fff;display:flex;flex-direction:column;flex-shrink:0;position:sticky;top:0;height:100vh;overflow-y:auto">
        <div style="padding:18px 16px;border-bottom:1px solid rgba(255,255,255,.1);font-weight:700;font-size:15px;flex-shrink:0">🎓 StudentTracker</div>
        <div style="margin:8px;padding:5px;background:rgba(255,255,255,.1);border-radius:6px;font-size:10px;text-align:center;color:rgba(255,255,255,.55);letter-spacing:1.5px">ADMIN</div>
        <nav style="flex:1;padding:8px">${nav}</nav>
        <div style="padding:12px 8px;border-top:1px solid rgba(255,255,255,.1);flex-shrink:0">
          <div style="font-size:12px;color:rgba(255,255,255,.45);padding:0 10px 8px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${esc(localStorage.getItem('username')||'')}</div>
          <button onclick="doLogout()" style="display:flex;align-items:center;gap:10px;padding:10px;width:100%;border-radius:8px;background:none;border:none;color:rgba(255,255,255,.65);font-size:14px;cursor:pointer">
            <span>⏏</span> Logout
          </button>
        </div>
      </aside>
      <main style="flex:1;padding:28px 32px;overflow-y:auto;min-width:0">
        ${contentHtml}
      </main>
    </div>
    <div id="_toast" style="position:fixed;bottom:24px;right:24px;padding:12px 20px;border-radius:10px;font-size:14px;font-weight:500;z-index:9999;opacity:0;pointer-events:none;transition:opacity .3s"></div>
    <div id="_modal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);align-items:center;justify-content:center;z-index:1000;padding:20px"></div>
  `;
  // re-attach modal close on backdrop click
  document.getElementById('_modal').addEventListener('click', e => {
    if (e.target === document.getElementById('_modal')) closeModal();
  });
}

async function doLogout() {
  try { await apiFetch('/auth/logout/', { method:'POST' }); } catch {}
  localStorage.clear();
  window.location.href = 'login.html';
}

// ── Modal helpers ─────────────────────────────────────────────────────────────
function openModal(html, width = 520) {
  const el = document.getElementById('_modal');
  if (!el) return;
  el.innerHTML = `<div style="background:#fff;border-radius:14px;width:100%;max-width:${width}px;max-height:90vh;overflow-y:auto;box-shadow:0 20px 60px rgba(0,0,0,.25)">${html}</div>`;
  el.style.display = 'flex';
}
function closeModal() {
  const el = document.getElementById('_modal');
  if (el) el.style.display = 'none';
}
function modalHeader(title) {
  return `<div style="display:flex;align-items:center;justify-content:space-between;padding:18px 22px;border-bottom:1px solid #e9ecef">
    <h2 style="font-size:16px;font-weight:600;color:#1a1a2e">${esc(title)}</h2>
    <button onclick="closeModal()" style="background:none;border:none;font-size:22px;color:#6c757d;cursor:pointer;line-height:1;padding:4px">×</button>
  </div>`;
}
function formField(label, inputHtml, required = false) {
  return `<div style="margin-bottom:14px">
    <label style="display:block;font-size:13px;font-weight:500;margin-bottom:5px;color:#495057">
      ${esc(label)}${required ? ' <span style="color:#e63946">*</span>' : ''}
    </label>
    ${inputHtml}
  </div>`;
}
const IS = `class="inp"`;
const SS = `class="inp"`;
const inputStyle = IS, selectStyle = SS;
