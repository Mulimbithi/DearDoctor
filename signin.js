// Step 1 of sign-in: check phone + password; the backend then sends a code.
document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("signin-form");
    const phoneInput = document.getElementById("phone");
    const errorBox = document.getElementById("form-error");
    const button = form.querySelector('button[type="submit"]');

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        errorBox.hidden = true;
        if (!form.reportValidity()) return;

        button.disabled = true;
        button.textContent = "Checking...";
        try {
            const phone = phoneInput.value.trim();
            await apiFetch("/auth/login", {
                method: "POST",
                body: { phone, password: document.getElementById("password").value }
            });
            sessionStorage.setItem(PHONE_KEY, phone);
            sessionStorage.setItem(PENDING_KEY, DataTransfer.pending_token);
            window.location.assign("otp.html");
        } catch (error) {
            errorBox.textContent = error.status === 422
                ? "Please check your phone number (for example 0712345678) and try again."
                : error.message;
            errorBox.hidden = false;
        } finally {
            button.disabled = false;
            button.textContent = "Sign in";
        }
    });
});