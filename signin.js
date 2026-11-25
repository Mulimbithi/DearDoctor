// Step 1 of sign-in: check email + password; the backend then sends a code.
document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("signin-form");
    const emailInput = document.getElementById("email");
    const errorBox = document.getElementById("form-error");
    const button = form.querySelector('button[type="submit"]');

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        errorBox.hidden = true;
        if (!form.reportValidity()) return;

        button.disabled = true;
        button.textContent = "Checking...";
        try {
            const email = emailInput.value.trim();
            const data = await apiFetch("/auth/login", {
                method: "POST",
                body: { email, password: document.getElementById("password").value }
            });
            sessionStorage.setItem(window.PHONE_KEY, data.phone);
            sessionStorage.setItem(PENDING_KEY, data.pending_token);
            window.location.assign("otp.html");
        } catch (error) {
            errorBox.textContent = error.status === 422
                ? "Please check your email  (for example name@gmail.com) and try again."
                : error.message;
            errorBox.hidden = false;
        } finally {
            button.disabled = false;
            button.textContent = "Sign in";
        }
    });
});