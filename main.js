document.addEventListener("DOMContentLoaded", () => {
//settings and helpers//
const CONFIG = {
  API_BASE: 'http://127.0.0.1:8000/api/v1',
  USE_MOCK: true,
  PAGES: { signin: 'signin.html', mother: 'mother.html', staff: 'staff.html',
           consultant: 'consultant.html', case: 'case.html' },
  MOCK_USER: { nickname: 'demo', password: 'Passw0rd!' }
};

async function api(path, options = {}) {
  if (CONFIG.USE_MOCK) return mockApi(path, options);
  const { method = 'GET', body } = options;
  const response = await fetch(CONFIG.API_BASE + path, {
    method,
    credentials: 'include',
    headers: body ? { 'Content-Type': 'application/json' } : undefined,
    body: body ? JSON.stringify(body) : undefined
  });
  let data = null;
  try { data = await response.json(); } catch (error) { /* no body */ }
  return { ok: response.ok, status: response.status, data };
}

//fake backend//
const MOCK_CASES = [
  { ref: 'C-101', risk: 'High',   nickname: 'sunny', age_range: '15-17', status: 'Open',
    assigned_at: '2026-11-10', score: 19, self_harm: true,  call_consent: true,  notes: [] },
  { ref: 'C-098', risk: 'High',   nickname: 'river', age_range: '18-19', status: 'In follow-up',
    assigned_at: '2026-11-08', score: 16, self_harm: false, call_consent: false,
    notes: [{ author: 'You', created_at: '2026-11-09 10:30', body: 'First contact made by text.' }] },
  { ref: 'C-095', risk: 'Medium', nickname: 'maple', age_range: '15-17', status: 'Open',
    assigned_at: '2026-11-07', score: 12, self_harm: false, call_consent: true,  notes: [] }
];
const summary = (c) => ({ ref: c.ref, risk: c.risk, nickname: c.nickname,
                          age_range: c.age_range, status: c.status, assigned_at: c.assigned_at });

async function mockApi(path, { method = 'GET', body } = {}) {
  await wait(300);
  if (!sessionStorage.getItem('mock_signed_in')) return { ok: false, status: 401, data: null };
  const parts = path.split('/').filter(Boolean);            // e.g. ['cases', 'C-101', 'notes']
  if (parts[0] === 'cases') {
    if (parts.length === 1 && method === 'GET') {
      const open = MOCK_CASES.filter((c) => c.status !== 'Closed');
      return { ok: true, status: 200, data: { max_cases: 4, cases: open.map(summary),
               notices: [{ id: 'n1', text: 'A case was closed because the mother left the service.' }] } };
    }
    const found = MOCK_CASES.find((c) => c.ref === decodeURIComponent(parts[1] || ''));
    if (!found) return { ok: false, status: 404, data: null };
    if (parts.length === 2 && method === 'GET') return { ok: true, status: 200, data: found };
    if (parts[2] === 'notes' && method === 'POST') {
      if (!body.body || !body.body.trim()) return { ok: false, status: 422, data: null };
      found.notes.push({ author: 'You', created_at: new Date().toISOString().slice(0, 16).replace('T', ' '), body: body.body });
      return { ok: true, status: 201, data: null };
    }
    if (parts[2] === 'close' && method === 'PATCH') { found.status = 'Closed'; return { ok: true, status: 200, data: null }; }
  }
  return { ok: false, status: 404, data: null };
}
//consultant page//
async function initConsultant() {
  const RISK_ORDER = { high: 0, medium: 1, low: 2 };
  const NAMES = { all: 'All', high: 'High', medium: 'Medium', low: 'Low' };
  const list      = $('case-list');
  const emptyMsg  = $('empty-message');
  const openCount = $('open-count');
  const highCount = $('high-count');
  const capNote   = $('capacity-note');
  const noticeBox = $('notices');
  const errorBox  = $('page-error');
  const chips     = document.querySelectorAll('.filters .chip');

  let allCases = [];
  let maxCases = 4;                 // the real value comes from the server
  let filter = 'all';

  const reveal = () => { document.body.style.visibility = 'visible'; };
  const showError = (message) => { errorBox.textContent = message; errorBox.hidden = false; };

  // ----- notices (dismissal is remembered in this browser only) -----
  function dismissed() {
    try { return JSON.parse(localStorage.getItem('dismissed_notices') || '[]'); } catch (e) { return []; }
  }
  function rememberDismissed(id) {
    const list = dismissed(); list.push(id);
    localStorage.setItem('dismissed_notices', JSON.stringify(list));
  }
  function renderNotices(notices) {
    noticeBox.replaceChildren();
    for (const n of notices.filter((x) => !dismissed().includes(x.id))) {
      const box = document.createElement('div'); box.className = 'notice';
      const text = document.createElement('span'); text.textContent = n.text;
      const btn = document.createElement('button');
      btn.type = 'button'; btn.className = 'close-btn'; btn.textContent = 'Dismiss';
      btn.addEventListener('click', () => {
        rememberDismissed(n.id);
        box.classList.add('fade-out');
        setTimeout(() => box.remove(), 400);
      });
      box.append(text, btn);
      noticeBox.appendChild(box);
    }
  }

  // ----- one case card (built with textContent, so typed text can never run as code) -----
  function caseCard(c) {
    const li = document.createElement('li');
    const a = document.createElement('a');
    a.className = 'case-card';
    a.href = `${CONFIG.PAGES.case}?ref=${encodeURIComponent(c.ref)}`;

    const info = document.createElement('div'); info.className = 'case-info';
    const head = document.createElement('div'); head.className = 'case-header-row';
    const id = document.createElement('span'); id.className = 'case-id'; id.textContent = c.ref;
    const badge = document.createElement('span');
    badge.className = 'badge ' + c.risk.toLowerCase(); badge.textContent = c.risk;
    head.append(id, badge);

    const sub = document.createElement('div'); sub.className = 'case-subtitle';
    sub.textContent = `${c.nickname}, ${c.age_range}`;
    const date = document.createElement('div'); date.className = 'case-date';
    date.textContent = `${c.status}, ${c.assigned_at}`;
    info.append(head, sub, date);

    const arrow = document.createElement('span');
    arrow.className = 'arrow-icon'; arrow.setAttribute('aria-hidden', 'true'); arrow.textContent = '\u203A';

    a.append(info, arrow);
    li.appendChild(a);
    return li;
  }

  // ----- draw the page from the data (this is where the filter works) -----
  function render() {
    const risk = (c) => c.risk.toLowerCase();
    const shown = allCases
      .filter((c) => filter === 'all' || risk(c) === filter)
      .sort((a, b) => (RISK_ORDER[risk(a)] - RISK_ORDER[risk(b)]) || a.assigned_at.localeCompare(b.assigned_at));

    list.replaceChildren(...shown.map(caseCard));

    emptyMsg.hidden = shown.length > 0;
    emptyMsg.textContent = allCases.length === 0
      ? 'No cases yet. New cases arrive by text message and then appear here.'
      : `No ${filter} risk cases right now.`;

    openCount.textContent = `${allCases.length} of ${maxCases}`;
    highCount.textContent = String(allCases.filter((c) => risk(c) === 'high').length);
    capNote.hidden = allCases.length < maxCases;
    capNote.textContent = `You have reached your limit of ${maxCases} open cases. New cases will go to another consultant or wait until you close one.`;

    chips.forEach((chip) => {
      const key = chip.dataset.filter;
      const n = key === 'all' ? allCases.length : allCases.filter((c) => risk(c) === key).length;
      chip.textContent = `${NAMES[key]} (${n})`;
    });
  }

  // ----- get the cases from the server -----
  async function load() {
    let result;
    try {
      result = await api('/cases');
    } catch (error) {
      showError('We could not reach the server. Please try again.'); reveal(); return;
    }
    if (result.status === 401 || result.status === 403) { go(CONFIG.PAGES.staff); return; }
    if (!result.ok) { showError('Something went wrong. Please try again later.'); reveal(); return; }

    errorBox.hidden = true;
    allCases = result.data.cases;
    maxCases = result.data.max_cases || 4;
    renderNotices(result.data.notices || []);
    render();
    reveal();
  }

  // ----- the filter buttons -----
  chips.forEach((chip) => {
    chip.addEventListener('click', () => {
      filter = chip.dataset.filter;
      chips.forEach((c) => {
        const on = c === chip;
        c.classList.toggle('active', on);
        c.setAttribute('aria-pressed', String(on));
      });
      render();                                  // no server call needed: the list is already loaded
    });
  });

  $('signout').addEventListener('click', async () => {
    await auth.signOut();
    go(CONFIG.PAGES.staff);
  });

  await load();
  setInterval(load, 60000);       // new cases arrive by text message, so refresh the list every minute
}
//case_deets js//
async function initCase() {
  const ref   = new URLSearchParams(location.search).get('ref');
  const path  = '/cases/' + encodeURIComponent(ref || '');
  const errorBox = $('page-error');
  const message  = $('action-message');

  const reveal = () => { document.body.style.visibility = 'visible'; };
  const showError = (m) => { errorBox.textContent = m; errorBox.hidden = false; };
  const showMessage = (m) => { message.textContent = m; message.hidden = false; };

  async function load() {
    if (!ref) { showError('No case selected.'); reveal(); return; }
    let result;
    try { result = await api(path); }
    catch (error) { showError('We could not reach the server. Please try again.'); reveal(); return; }

    if (result.status === 401 || result.status === 403) { go(CONFIG.PAGES.staff); return; }
    if (result.status === 404) { showError('Case not found.'); reveal(); return; }   // also shown for cases that are not yours
    if (!result.ok) { showError('Something went wrong. Please try again later.'); reveal(); return; }

    const c = result.data;
    $('case-title').textContent = 'Case ' + c.ref;
    const badge = $('case-badge');
    badge.textContent = c.risk; badge.className = 'badge ' + c.risk.toLowerCase();
    $('f-nickname').textContent = c.nickname;
    $('f-age').textContent = c.age_range;
    $('f-score').textContent = c.score + ' of 30';
    $('f-selfharm').textContent = c.self_harm ? 'Yes' : 'No';
    $('f-status').textContent = c.status;
    $('f-assigned').textContent = c.assigned_at;

    const ul = $('notes-list'); ul.replaceChildren();
    for (const n of c.notes) {
      const li = document.createElement('li'); li.className = 'case-card';
      li.textContent = `${n.author}, ${n.created_at}: ${n.body}`;
      ul.appendChild(li);
    }

    const closed = c.status === 'Closed';
    ['save-note', 'close-case'].forEach((id) => { if (closed) $(id).disabled = true; });
    reveal();
  }

  async function send(subPath, method, body, okText) {
    errorBox.hidden = true; message.hidden = true;
    let result;
    try { result = await api(path + subPath, { method, body }); }
    catch (error) { showError('We could not reach the server. Please try again.'); return null; }
    if (result.status === 401) { go(CONFIG.PAGES.staff); return null; }
    if (result.status === 403) { showError('That is not allowed for this case.'); return null; }
    if (result.status === 422) { showError('Please check what you typed and try again.'); return null; }
    if (!result.ok) { showError('Something went wrong. Please try again.'); return null; }
    if (okText) showMessage(okText);
    return result;
  }

  $('save-note').addEventListener('click', async () => {
    const text = $('note-text').value.trim();
    if (!text) { showError('Please write a note first.'); return; }
    if (await send('/notes', 'POST', { body: text }, 'Note saved.')) { $('note-text').value = ''; load(); }
  });

  $('close-case').addEventListener('click', async () => {
    if (!window.confirm('Close this case? You cannot reopen it.')) return;
    if (await send('/close', 'PATCH', { reason: $('close-reason').value })) go(CONFIG.PAGES.consultant);
  });

  await load();
}


    const welcomeElement = document.getElementById("welcomeMessage");
    if (welcomeElement) {
        const isReturningVisitor = localStorage.getItem("returning_visitor");
        if (isReturningVisitor) {
            welcomeElement.textContent = "Welcome back! Great to see you again.";
        } else {
            welcomeElement.textContent = "Welcome! Let's chat!";
            localStorage.setItem("returning_visitor", "true");
        }
    }

    const deletionDialog = document.getElementById("deletion-dialog");
    const deletionForm = document.getElementById("deletion-form");
    const deletionPassword = document.getElementById("deletion-password");
    const deletionStatus = document.getElementById("deletion-status");
    const submitDeletion = document.getElementById("submit-deletion");
    const cancelDeletionRequest = document.getElementById("cancel-deletion-request");
    const openDeletionDialog = document.getElementById("open-deletion-dialog");
    const logoutButton = document.getElementById("logout-button");

    if (!deletionDialog || !deletionForm || !openDeletionDialog || !logoutButton) {
        return;
    }

    const tokenKey = "deardoctor_access_token";
    const apiBaseUrl = (window.DEARDOCTOR_API_BASE_URL || "http://127.0.0.1:8000/api/v1").replace(/\/+$/, "");
    let deletionRequestSent = false;

    async function sendRequest(path, method, body) {
        const token = sessionStorage.getItem(tokenKey);
        if (!token) {
            throw new Error("Your session has expired. Sign in again before changing your account.");
        }

        let response;
        try {
            response = await fetch(`${apiBaseUrl}${path}`, {
                method,
                headers: {
                    Accept: "application/json",
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`
                },
                body: body === undefined ? undefined : JSON.stringify(body)
            });
        } catch {
            throw new Error("Could not reach the server. Please try again later.");
        }

        const contentType = response.headers.get("content-type") || "";
        const data = contentType.includes("application/json") ? await response.json() : {};
        if (!response.ok) {
            const detail = data.detail || data.message;
            throw new Error(typeof detail === "string" ? detail : "The request could not be completed.");
        }
        return data;
    }

    function showDeletionState(isPending) {
        deletionRequestSent = isPending;
        deletionPassword.value = "";
        deletionPassword.hidden = isPending;
        deletionForm.querySelector('label[for="deletion-password"]').hidden = isPending;
        submitDeletion.hidden = isPending;
        cancelDeletionRequest.hidden = !isPending;
    }

    openDeletionDialog.addEventListener("click", async () => {
        deletionStatus.textContent = "";
        showDeletionState(false);
        deletionDialog.showModal();
        deletionPassword.focus();

        try {
            const result = await sendRequest("/me/deletion-request", "GET");
            const pending = result.pending === true ||
                result.requested === true ||
                result.status === "pending" ||
                Boolean(result.requested_at);
            if (pending) {
                showDeletionState(true);
                deletionStatus.textContent = result.message ||
                    "Your deletion request is pending. You can cancel it during the 7-day waiting period.";
            }
        } catch (error) {
            deletionStatus.textContent = error.message;
        }
    });

    document.getElementById("cancel-deletion").addEventListener("click", () => {
        deletionDialog.close();
    });

    deletionForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        deletionStatus.textContent = "";
        submitDeletion.disabled = true;
        submitDeletion.textContent = "Sending request...";

        try {
            const result = await sendRequest("/me/deletion-request", "POST", {
                password: deletionPassword.value
            });
            showDeletionState(true);
            deletionStatus.textContent = result.message ||
                "Your deletion request was received. Your account is scheduled for deletion after 7 days. You can cancel it during the waiting period.";
        } catch (error) {
            deletionStatus.textContent = error.message;
        } finally {
            submitDeletion.disabled = false;
            submitDeletion.textContent = "Request deletion";
        }
    });

    cancelDeletionRequest.addEventListener("click", async () => {
        cancelDeletionRequest.disabled = true;
        deletionStatus.textContent = "Cancelling your deletion request...";
        try {
            const result = await sendRequest("/me/deletion-request/cancel", "POST");
            showDeletionState(false);
            deletionStatus.textContent = result.message || "Your deletion request has been cancelled.";
        } catch (error) {
            deletionStatus.textContent = error.message;
        } finally {
            cancelDeletionRequest.disabled = false;
        }
    });

    logoutButton.addEventListener("click", async () => {
        logoutButton.disabled = true;
        logoutButton.textContent = "Signing out...";
        try {
            await sendRequest("/logout", "POST");
            sessionStorage.removeItem(tokenKey);
            window.location.assign("signin.html");
        } catch (error) {
            logoutButton.disabled = false;
            logoutButton.textContent = "Sign out";
            const chatStatus = document.querySelector(".chat-bubble");
            if (chatStatus) chatStatus.textContent = error.message;
        }
        //to here//
    });
});
