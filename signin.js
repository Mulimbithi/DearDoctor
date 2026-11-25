// Step 1 of sign-in: check phone + password; the backend then sends a code.
document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("signin-form");
    const emailInput = document.getElementById("email");
    const errorBox = document.getElementById("form-error");
    const button = form.querySelector('button[type="submit"]');
    const infoBox = document.getElementById("form-info");

    // coming from the register page: welcome her and fill in her email
    if (new URLSearchParams(location.search).get("registered") === "1") {
        infoBox.textContent = "Your account has been created. Sign in with your password to continue. We will then send a code to your email.";
        infoBox.hidden = false;
        try {
            const saved = sessionStorage.getItem("deardoctor_new_email");
            if (saved) { emailInput.value = saved; sessionStorage.removeItem("deardoctor_new_email"); }
        } catch (e) { /* nothing to fill in */ }
    }

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        errorBox.hidden = true;
        if (!form.reportValidity()) return;

        button.disabled = true;
        button.textContent = "Checking...";
        try {
            const data = await apiFetch("/auth/login", {
                method: "POST",
                body: {
                    email: emailInput.value.trim(),
                    password: document.getElementById("password").value
                }
            });
            // the backend sends back the phone the code was sent to; the next page needs it
            sessionStorage.setItem(PHONE_KEY, data.phone);
            sessionStorage.setItem(PENDING_KEY, data.pending_token);
            window.location.assign("otp.html");
        } catch (error) {
            errorBox.textContent = error.status === 422
                ? "Please check your email address and try again."
                : error.message;
            errorBox.hidden = false;
        } finally {
            button.disabled = false;
            button.textContent = "Sign in";
        }
    });
});