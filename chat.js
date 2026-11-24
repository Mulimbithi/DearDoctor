document.addEventListener("DOMContentLoaded", () => {
    const log = document.getElementById("chat-log");
    const optionsBox = document.getElementById("chat-options");
    const errorBox = document.getElementById("chat-error");
    const form = document.getElementById("chat-form");
    const textInput = document.getElementById("chat-text");

    let sessionId = null;
    let currentNode = null;   // the node whose buttons are showing

    function showError(message) { errorBox.textContent = message; errorBox.hidden = false; }

    function addBubble(text, mine) {
        const div = document.createElement("div");
        div.className = "chat-bubble" + (mine ? " me" : "");
        div.textContent = text;            // textContent: typed text can never run as code
        log.appendChild(div);
        div.scrollIntoView({ behavior: "smooth", block: "end" });
    }

    function showOptions(options, onPick) {
        optionsBox.replaceChildren();
        for (const option of options) {
            const b = document.createElement("button");
            b.type = "button";
            b.className = "topic-btn";
            b.textContent = option.label;
            b.addEventListener("click", () => onPick(option));
            optionsBox.appendChild(b);
        }
    }
    //what happens when the epds is done and users want to exit it
    function showEnd() {
        optionsBox.replaceChildren();
        const again = document.createElement("button");
        again.type = "button";
        again.className = "topic-btn";
        again.textContent = "Start a new check-in";
        again.addEventListener("click", start);

        const out = document.createElement("button");
        out.type = "button";
        out.className = "topic-btn";
        out.style.background = "#666666";
        out.textContent = "Sign out";
        out.addEventListener("click", signOut);

        optionsBox.append(again, out);
    }

    function signOut() {
        clearSession();
        window.location.assign("signin.html");
    }

    // Draw whatever the backend sent: a normal node or an EPDS question.
    function render(payload) {
        errorBox.hidden = true;
        if (payload.type === "epds") {
            currentNode = null;
            addBubble(`(${payload.item} of 10) ${payload.text}`, false);
            showOptions(payload.options, (o) => answerEpds(payload.item, o));
        } else {
            currentNode = payload.node;
            addBubble(payload.text, false);
            showOptions(payload.options || [], (o) => choose(payload.node, o));
        }
    }

    async function call(path, body) {
        try {
            render(await apiFetch(path, { method: "POST", body, auth: true }));
        } catch (error) {
            showError(error.message);
        }
    }

    function choose(node, option) {
        addBubble(option.label, true);
        optionsBox.replaceChildren();
        call("/chat/choose", { session_id: sessionId, node, choice: option.id, lang: "en" });
    }

    function answerEpds(item, option) {
        addBubble(option.label, true);
        optionsBox.replaceChildren();
        call("/chat/epds", { session_id: sessionId, item, option: option.id, lang: "en" });
    }

    async function start() {
        log.replaceChildren();
        optionsBox.replaceChildren();
        errorBox.hidden = true;
        try {
            const data = await apiFetch("/chat/start?lang=en", { method: "POST", auth: true });
            sessionId = data.session_id;
            render({ type: "node", node: data.node, text: data.text, options: data.options });
        } catch (error) {
            showError(error.message);
        }
    }

    form.addEventListener("submit", (event) => {
        event.preventDefault();
        const text = textInput.value.trim();
        if (!text || sessionId === null) return;
        textInput.value = "";
        addBubble(text, true);
        optionsBox.replaceChildren();
        call("/chat/message", { session_id: sessionId, text, lang: "en" });
    });

    document.getElementById("new-chat").addEventListener("click", (event) => {
        event.preventDefault();
        start();
    });
    document.getElementById("logout-button").addEventListener("click", (event) => {
        event.preventDefault();
        clearSession();
        window.location.assign("signin.html");
    });

    start();
});