// One case: details, notes, and closing it.
document.addEventListener("DOMContentLoaded", () => {
    const $ = (id) => document.getElementById(id);

    const BADGE_CLASS = { urgent: "high", high: "high", moderate: "medium", low: "low" };
    const TRIGGERS = {
        item10_positive: "Self-harm answer on the screening",
        epds_high: "High screening score",
        requested_by_mother: "She asked to talk to a counsellor"
    };

    const ref = new URLSearchParams(location.search).get("ref");
    const path = "/consultant/cases/" + encodeURIComponent(ref || "");
    const errorBox = $("page-error");
    const message = $("action-message");

    const reveal = () => { document.body.style.visibility = "visible"; };
    const showError = (m) => { errorBox.textContent = m; errorBox.hidden = false; };
    const showMessage = (m) => { message.textContent = m; message.hidden = false; };
    const cap = (s) => s ? s.charAt(0).toUpperCase() + s.slice(1) : "";

    function goToSignIn() { clearSession(); window.location.assign("signin.html"); }

    function handle(error) {
        if (error.status === 401 || error.status === 403) { goToSignIn(); return; }
        if (error.status === 404) { showError("Case not found."); return; }
        showError(error.message);
    }

    async function load() {
        if (!ref) { showError("No case selected."); reveal(); return; }
        try {
            const c = await apiFetch(path, { auth: true });
            $("case-title").textContent = "Case " + c.ref;
            const badge = $("case-badge");
            badge.textContent = c.risk;
            badge.className = "badge " + (BADGE_CLASS[c.risk.toLowerCase()] || "low");
            $("f-nickname").textContent = c.nickname;
            $("f-age").textContent = c.age_range;
            $("f-score").textContent = c.score === null ? "Not recorded" : c.score + " of 30";
            $("f-selfharm").textContent = c.self_harm ? "Yes" : "No";
            $("f-trigger").textContent = TRIGGERS[c.trigger] || c.trigger || "";
            $("f-status").textContent = cap(c.status);
            $("f-assigned").textContent = c.assigned_at;
            $("call-consent-warning").hidden = c.call_consent === true;

            const ul = $("notes-list"); ul.replaceChildren();
            for (const n of c.notes) {
                const li = document.createElement("li"); li.className = "case-card";
                li.textContent = `${n.author}, ${n.created_at}: ${n.body}`;
                ul.appendChild(li);
            }

            const closed = c.status === "closed";
            ["save-note", "close-case", "note-text", "close-reason"].forEach((id) => { $(id).disabled = closed; });
            if (closed) showMessage("This case is closed.");
            errorBox.hidden = true;
        } catch (error) {
            handle(error);
        }
        reveal();
    }

    $("save-note").addEventListener("click", async () => {
        errorBox.hidden = true; message.hidden = true;
        const text = $("note-text").value.trim();
        if (!text) { showError("Please write a note first."); return; }
        try {
            await apiFetch(path + "/notes", { method: "POST", auth: true, body: { body: text } });
            $("note-text").value = "";
            showMessage("Note saved.");
            load();
        } catch (error) { handle(error); }
    });

    $("close-case").addEventListener("click", async () => {
        if (!window.confirm("Close this case? You cannot reopen it.")) return;
        errorBox.hidden = true; message.hidden = true;
        try {
            // the reason is saved as the last note, then the case is closed
            await apiFetch(path + "/notes", {
                method: "POST", auth: true,
                body: { body: "Case closed. Reason: " + $("close-reason").value }
            });
            await apiFetch(path + "/close", { method: "PATCH", auth: true });
            window.location.assign("consultant.html");
        } catch (error) { handle(error); }
    });

    load();
});