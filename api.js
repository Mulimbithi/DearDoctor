// api.js - shared helpers. Load this BEFORE the page's own script.
const API_BASE = "http://127.0.0.1:8000/api";
const TOKEN_KEY = "deardoctor_access_token";
window.PHONE_KEY = "deardoctor_phone";
const PENDING_KEY = "deardoctor_pending";

function getToken() { return sessionStorage.getItem(TOKEN_KEY); }
function saveToken(token) { sessionStorage.setItem(TOKEN_KEY, token); }
function clearSession() {
    sessionStorage.removeItem(TOKEN_KEY);
    sessionStorage.removeItem(window.PHONE_KEY);
}

// Sends a request to the backend. Throws an Error (with .status) if it fails.
async function apiFetch(path, { method = "GET", body, auth = false } = {}) {
    const headers = { Accept: "application/json" };
    if (body !== undefined) headers["Content-Type"] = "application/json";

    if (auth) {
        // auth can be true (use the saved sign-in token) or a token string
        const token = typeof auth === "string" ? auth : getToken();
        if (!token) {
            window.location.assign("signin.html");
            throw new Error("Please sign in first.");
        }
        headers.Authorization = "Bearer " + token;
    }

    let response;
    try {
        response = await fetch(API_BASE + path, {
            method,
            headers,
            body: body === undefined ? undefined : JSON.stringify(body)
        });
    } catch {
        throw new Error("Could not reach the server. Please try again later.");
    }

    let data = {};
    try { data = await response.json(); } catch { /* no body */ }

    if (!response.ok) {
        if (auth === true && response.status === 401) {
            clearSession();
            window.location.assign("signin.html");
        }
        let detail = data.detail;
        if (Array.isArray(detail)) detail = "Please check what you typed and try again.";
        const error = new Error(typeof detail === "string" ? detail : "The request could not be completed.");
        error.status = response.status;
        throw error;
    }
    return data;
}