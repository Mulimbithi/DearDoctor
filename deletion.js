// Account deletion dialog for mothers.
// Backend routes (to be built):
//   GET  /api/mother/deletion-request          -> {pending: true/false, message}
//   POST /api/mother/deletion-request          body {password}
//   POST /api/mother/deletion-request/cancel
document.addEventListener("DOMContentLoaded", () => {
    const dialog = document.getElementById("deletion-dialog");
    const form = document.getElementById("deletion-form");
    const passwordInput = document.getElementById("deletion-password");
    const status = document.getElementById("deletion-status");
    const submitButton = document.getElementById("submit-deletion");
    const cancelRequestButton = document.getElementById("cancel-deletion-request");

    const NOT_READY = "Account deletion is not switched on yet. Please try again later.";

    function showPending(isPending) {
        passwordInput.value = "";
        passwordInput.hidden = isPending;
        form.querySelector('label[for="deletion-password"]').hidden = isPending;
        submitButton.hidden = isPending;
        cancelRequestButton.hidden = !isPending;
    }

    function messageFor(error) {
        return (error.status === 404 || error.status === 405) ? NOT_READY : error.message;
    }

    document.getElementById("open-deletion-dialog").addEventListener("click", async (event) => {
        event.preventDefault();
        status.textContent = "";
        showPending(false);
        dialog.showModal();
        passwordInput.focus();
        try {
            const result = await apiFetch("/mother/deletion-request", { auth: true });
            if (result.pending) {
                showPending(true);
                status.textContent = result.message ||
                    "Your deletion request is pending. You can cancel it during the 7-day waiting period.";
            } else if (result.deleted) {
                clearSession();
                status.textContent = result.message || "Your account has been deleted.";
                window.setTimeout(() => window.location.assign("signin.html"), 1500);
            }
        } catch (error) {
            status.textContent = messageFor(error);
        }
    });

    document.getElementById("cancel-deletion").addEventListener("click", () => dialog.close());

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        status.textContent = "";
        submitButton.disabled = true;
        submitButton.textContent = "Sending request...";
        try {
            const result = await apiFetch("/mother/deletion-request", {
                method: "POST", auth: true, body: { password: passwordInput.value }
            });
            showPending(true);
            status.textContent = result.message ||
                "Your request was received. Your account will be deleted after 7 days. You can cancel during the waiting period.";
        } catch (error) {
            status.textContent = messageFor(error);
        } finally {
            submitButton.disabled = false;
            submitButton.textContent = "Request deletion";
        }
    });

    cancelRequestButton.addEventListener("click", async () => {
        status.textContent = "Cancelling your deletion request...";
        try {
            const result = await apiFetch("/mother/deletion-request/cancel", { method: "POST", auth: true });
            showPending(false);
            status.textContent = result.message || "Your deletion request has been cancelled.";
        } catch (error) {
            status.textContent = messageFor(error);
        }
    });
});