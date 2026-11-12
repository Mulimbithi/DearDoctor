document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("signin-form");
    const usernameInput = document.getElementById("username");
    const passwordInput = document.getElementById("password");
    const errorMessage = document.getElementById("form-error");

    if (!form || !usernameInput || !passwordInput || !errorMessage) {
        return;
    }

    const submitButton = form.querySelector('button[type="submit"]');
    const tokenKey = "deardoctor_access_token";
    const apiBaseUrl = (window.DEARDOCTOR_API_BASE_URL || "http://127.0.0.1:8000/api/v1")
        .replace(/\/+$/, "");

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        errorMessage.textContent = "";
        errorMessage.hidden = true;

        if (!form.reportValidity()) {
            return;
        }

        submitButton.disabled = true;
        submitButton.textContent = "Signing in...";

        try {
            let response;
            try {
                response = await fetch(`${apiBaseUrl}/auth/login`, {
                    method: "POST",
                    headers: {
                        Accept: "application/json",
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        username: usernameInput.value.trim(),
                        password: passwordInput.value
                    })
                });
            } catch {
                throw new Error("Could not reach the sign-in service. Please try again later.");
            }

            const contentType = response.headers.get("content-type") || "";
            const data = contentType.includes("application/json")
                ? await response.json()
                : {};

            if (!response.ok) {
                const detail = data.detail || data.message;
                throw new Error(typeof detail === "string"
                    ? detail
                    : "Sign-in failed. Check your username and password and try again.");
            }

            if (typeof data.access_token !== "string" || !data.access_token) {
                throw new Error("The sign-in service returned an invalid response.");
            }

            sessionStorage.setItem(tokenKey, data.access_token);
            window.location.assign("mother.html");
        } catch (error) {
            errorMessage.textContent = error.message || "Sign-in failed. Please try again.";
            errorMessage.hidden = false;
        } finally {
            submitButton.disabled = false;
            submitButton.textContent = "Sign In";
        }
    });
});
