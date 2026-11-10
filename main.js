document.addEventListener("DOMContentLoaded", () => {
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

    const dismissButton = document.getElementById("closeNotification");
    const noticeSection = document.querySelector(".notice-section");
    if (dismissButton && noticeSection) {
        dismissButton.addEventListener("click", () => {
            noticeSection.classList.add("fade-out");
            noticeSection.addEventListener("transitionend", () => noticeSection.remove(), { once: true });
        });
    }
    //fix code from here//
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
