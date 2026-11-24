// Step 2 of sign-in: send the phone number and the code, get a token back.
document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("otp-form");
    const codeInput = document.getElementById("otp");
    const errorBox = document.getElementById("form-error");
    const infoBox = document.getElementById("form-info");
    const resend = document.getElementById("resend");
    const button = form.querySelector('button[type="submit"]');
    const phone = sessionStorage.getItem(PHONE_KEY);

    if (!phone) { window.location.assign("signin.html"); return; }

    const HOME = { mother: "mother.html", consultant: "consultant.html", admin: "admin.html" };

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        errorBox.hidden = true; infoBox.hidden = true;
        button.disabled = true;
        button.textContent = "Checking...";
        try {
            const data = await apiFetch("/auth/verify-otp", {
                method: "POST",
                body: { phone, code: codeInput.value.trim() }
            });
            saveToken(data.token);
            sessionStorage.removeItem(PHONE_KEY);
            sessionStorage.removeItem(PENDING_KEY);
            window.location.assign(HOME[data.role] || "signin.html");
        } catch (error) {
            errorBox.textContent = error.message;
            errorBox.hidden = false;
        } finally {
            button.disabled = false;
            button.textContent = "Verify and sign in";
        }
    });

    resend.addEventListener("click", async (event) => {
        event.preventDefault();
        errorBox.hidden = true; infoBox.hidden = true;
        try {
            await apiFetch("/auth/resend-otp", {
                method: "POST",
                auth: sessionStorage.getItem(PENDING_KEY) || ""
            });
            infoBox.textContent = "A new code has been sent.";
            infoBox.hidden = false;
        } catch (error) {
            errorBox.textContent = error.status === 401
                ? "Please start again from the sign-in page."
                : error.message;
            errorBox.hidden = false;
        }
    });
});