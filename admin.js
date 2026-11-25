// Admin: consultants list, add a consultant, pause or reactivate one.
document.addEventListener("DOMContentLoaded", () => {
    const $ = (id) => document.getElementById(id);
    const rows = $("consultant-rows");
    const errorBox = $("page-error");
    const formMessage = $("form-message");
    const formError = $("form-error");
    const sendInviteButton = $("send-invite");
    const retryInviteButton = $("retry-invite");
    let pendingInviteId = null;

    const cap = (s) => s ? s.charAt(0).toUpperCase() + s.slice(1) : "";
    function goToSignIn() { clearSession(); window.location.assign("signin.html"); }

    function handle(error, box) {
        if (error.status === 401 || error.status === 403) { goToSignIn(); return; }
        (box || errorBox).textContent = error.message;
        (box || errorBox).hidden = false;
    }

    function rowFor(c) {
        const tr = document.createElement("tr");
        const name = document.createElement("td"); name.textContent = c.name;
        const status = document.createElement("td"); status.textContent = cap(c.status);
        const open = document.createElement("td"); open.textContent = String(c.open_cases);
        const action = document.createElement("td"); action.className = "text-right";
        const btn = document.createElement("button");
        btn.type = "button"; btn.className = "nav-btn";
        const pausing = c.status === "active";
        btn.textContent = pausing ? "Pause" : "Reactivate";
        btn.addEventListener("click", () => change(c, pausing, btn));
        action.appendChild(btn);
        tr.append(name, status, open, action);
        return tr;
    }

    async function load() {
        try {
            const data = await apiFetch("/admin/consultants", { auth: true });
            errorBox.hidden = true;
            rows.replaceChildren(...data.consultants.map(rowFor));
            if (data.consultants.length === 0) {
                const tr = document.createElement("tr");
                const td = document.createElement("td");
                td.colSpan = 4; td.textContent = "No consultants yet.";
                tr.appendChild(td); rows.appendChild(tr);
            }
        } catch (error) { handle(error); }
    }

    async function change(c, pausing, btn) {
        if (pausing && !window.confirm(
            `Pause ${c.name}? She will not be able to sign in, and her ${c.open_cases} open case(s) will move to other consultants.`)) return;
        btn.disabled = true;
        errorBox.hidden = true;
        try {
            await apiFetch(`/admin/consultants/${c.id}/${pausing ? "pause" : "reactivate"}`,
                           { method: "POST", auth: true });
            await load();
        } catch (error) { handle(error); btn.disabled = false; }
    }

    $("send-invite").addEventListener("click", async () => {
        formError.hidden = true; formMessage.hidden = true;
        const name = $("c-name").value.trim();
        const email = $("c-email").value.trim();
        const phone = $("c-phone").value.trim();
        if (!name || !email || !phone || !$("c-email").validity.valid) {
            formError.textContent = "Please enter a name, a valid email address, and a phone number.";
            formError.hidden = false; return;
        }
        sendInviteButton.disabled = true;
        sendInviteButton.textContent = "Sending invite...";
        try {
            const result = await apiFetch("/admin/consultants", {
                method: "POST", auth: true, body: { name, email, phone }
            });
            pendingInviteId = result.invite_sent ? null : result.consultant.id;
            retryInviteButton.hidden = result.invite_sent;
            formMessage.textContent = result.invite_sent
                ? "Account created and invite sent."
                : "Account created, but the invite email could not be sent. Retry to send a new temporary password.";
            formMessage.hidden = false;
            $("c-name").value = ""; $("c-email").value = ""; $("c-phone").value = "";
            await load();
        } catch (error) {
            if (error.status === 422) {
                formError.textContent = "Please check the email and the phone number (for example 0712345678).";
                formError.hidden = false;
            } else { handle(error, formError); }
        } finally {
            sendInviteButton.disabled = pendingInviteId !== null;
            sendInviteButton.textContent = "Send invite";
        }
    });

    retryInviteButton.addEventListener("click", async () => {
        if (pendingInviteId === null) return;
        formError.hidden = true; formMessage.hidden = true;
        retryInviteButton.disabled = true;
        retryInviteButton.textContent = "Retrying invite...";
        try {
            const result = await apiFetch(`/admin/consultants/${pendingInviteId}/invite`,
                                          { method: "POST", auth: true });
            if (result.invite_sent) {
                formMessage.textContent = "Invite email sent with a new temporary password.";
                formMessage.hidden = false;
                pendingInviteId = null;
                retryInviteButton.hidden = true;
                sendInviteButton.disabled = false;
                await load();
            } else {
                formMessage.textContent = "The invite email still could not be sent. Check the SMTP settings and retry.";
                formMessage.hidden = false;
            }
        } catch (error) { handle(error, formError); }
        finally {
            retryInviteButton.disabled = false;
            retryInviteButton.textContent = "Retry invite";
        }
    });

    $("signout").addEventListener("click", (e) => { e.preventDefault(); goToSignIn(); });

    load();
});