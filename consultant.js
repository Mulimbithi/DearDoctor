// Consultant case list: loads this consultant's open cases from the backend.
document.addEventListener("DOMContentLoaded", () => {
    const $ = (id) => document.getElementById(id);

    const RISK_ORDER = { urgent: 0, high: 1, moderate: 2, low: 3 };
    const BADGE_CLASS = { urgent: "high", high: "high", moderate: "medium", low: "low" };
    const NAMES = { all: "All", urgent: "Urgent", high: "High", moderate: "Moderate", low: "Low" };

    const list = $("case-list");
    const emptyMsg = $("empty-message");
    const openCount = $("open-count");
    const highCount = $("high-count");
    const capNote = $("capacity-note");
    const noticeBox = $("notices");
    const errorBox = $("page-error");
    const chips = document.querySelectorAll(".filters .chip");

    let allCases = [];
    let maxCases = 4;
    let filter = "all";

    const risk = (c) => c.risk.toLowerCase();
    const refNumber = (c) => parseInt(c.ref.replace("C-", ""), 10);
    const showError = (message) => { errorBox.textContent = message; errorBox.hidden = false; };

    function goToSignIn() { clearSession(); window.location.assign("signin.html"); }

    // ----- notices (dismissal is remembered in this browser only) -----
    function dismissed() {
        try { return JSON.parse(localStorage.getItem("dismissed_notices") || "[]"); }
        catch (e) { return []; }
    }
    function rememberDismissed(id) {
        try {
            const items = dismissed(); items.push(id);
            localStorage.setItem("dismissed_notices", JSON.stringify(items));
        } catch (e) { /* storage unavailable: the notice just comes back */ }
    }
    function renderNotices(notices) {
        noticeBox.replaceChildren();
        for (const n of notices.filter((x) => !dismissed().includes(x.id))) {
            const box = document.createElement("div"); box.className = "notice";
            const text = document.createElement("span"); text.textContent = n.text;
            const btn = document.createElement("button");
            btn.type = "button"; btn.className = "close-btn"; btn.textContent = "Dismiss";
            btn.addEventListener("click", () => {
                rememberDismissed(n.id);
                box.classList.add("fade-out");
                setTimeout(() => box.remove(), 400);
            });
            box.append(text, btn);
            noticeBox.appendChild(box);
        }
    }

    // ----- one case card (textContent only, so typed text can never run as code) -----
    function caseCard(c) {
        const li = document.createElement("li");
        const a = document.createElement("a");
        a.className = "case-card";
        a.href = "case_deets.html?ref=" + encodeURIComponent(c.ref);

        const info = document.createElement("div"); info.className = "case-info";
        const head = document.createElement("div"); head.className = "case-header-row";
        const id = document.createElement("span"); id.className = "case-id"; id.textContent = c.ref;
        const badge = document.createElement("span");
        badge.className = "badge " + (BADGE_CLASS[risk(c)] || "low");
        badge.textContent = c.risk;
        head.append(id, badge);

        const sub = document.createElement("div"); sub.className = "case-subtitle";
        sub.textContent = `${c.nickname}, ${c.age_range}`;
        const date = document.createElement("div"); date.className = "case-date";
        date.textContent = `${c.status}, ${c.assigned_at}`;
        info.append(head, sub, date);

        const arrow = document.createElement("span");
        arrow.className = "arrow-icon"; arrow.setAttribute("aria-hidden", "true"); arrow.textContent = "›";

        a.append(info, arrow);
        li.appendChild(a);
        return li;
    }

    function render() {
        const shown = allCases
            .filter((c) => filter === "all" || risk(c) === filter)
            .sort((a, b) =>
                (RISK_ORDER[risk(a)] - RISK_ORDER[risk(b)]) ||
                a.assigned_at.localeCompare(b.assigned_at) ||
                (refNumber(a) - refNumber(b)));

        list.replaceChildren(...shown.map(caseCard));

        emptyMsg.hidden = shown.length > 0;
        emptyMsg.textContent = allCases.length === 0
            ? "No cases yet. New cases appear here when a mother needs support."
            : `No ${filter} risk cases right now.`;

        openCount.textContent = `${allCases.length} of ${maxCases}`;
        highCount.textContent = String(allCases.filter((c) => ["urgent", "high"].includes(risk(c))).length);
        capNote.hidden = allCases.length < maxCases;
        capNote.textContent = `You have reached your limit of ${maxCases} open cases. New cases will go to another consultant or wait until you close one.`;

        chips.forEach((chip) => {
            const key = chip.dataset.filter;
            const n = key === "all" ? allCases.length : allCases.filter((c) => risk(c) === key).length;
            chip.textContent = `${NAMES[key]} (${n})`;
        });
    }

    async function load() {
        try {
            const data = await apiFetch("/consultant/cases", { auth: true });
            errorBox.hidden = true;
            allCases = data.cases;
            maxCases = data.max_cases || 4;
            renderNotices(data.notices || []);
            render();
        } catch (error) {
            if (error.status === 403) { goToSignIn(); return; }
            showError(error.message);
        }
    }

    chips.forEach((chip) => {
        chip.addEventListener("click", () => {
            filter = chip.dataset.filter;
            chips.forEach((c) => {
                const on = c === chip;
                c.classList.toggle("active", on);
                c.setAttribute("aria-pressed", String(on));
            });
            render();   // the list is already loaded, no server call needed
        });
    });

    $("signout").addEventListener("click", goToSignIn);

    load();
    setInterval(load, 60000);   // new cases arrive by themselves, so refresh every minute
});