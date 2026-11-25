document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("registration-form");
    const errorBox = document.getElementById("form-error");
    const button = form.querySelector('button[type="submit"]');

    function showError(message) { errorBox.textContent = message; errorBox.hidden = false; }

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        errorBox.hidden = true;
        if (!form.reportValidity()) return;

        if (!form.elements["data-storage"].checked) {
            showError("You need to agree to data storage to create an account.");
            return;
        }

        if (form.elements["password"].value !== form.elements["confirm-password"].value) {
            showError("The two passwords do not match.");
            return;
        }

        button.disabled = true;
        button.textContent = "Creating account...";
        try {
            const data = await apiFetch("/mother/register", {
                method: "POST",
                body: {
                    pseudonym: form.elements["username"].value.trim(),
                    age_range: form.elements["age-range"].value,
                    phone: form.elements["phone"].value.trim(),
                    email: form.elements["email"].value.trim(),
                    password: form.elements["password"].value,
                    consent: true,
                    sms_opt_in: form.elements["sms-notifications"].checked
                }
            });
            saveToken(data.token);
            window.location.assign("mother.html");
        } catch (error) {
            if (error.status === 422) {
                showError("Please check your phone number, email address, and password (at least 8 characters).");
            } else {
                showError(error.message);
            }
        } finally {
            button.disabled = false;
            button.textContent = "Create Account";
        }
    });
});