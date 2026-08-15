(() => {
  const transcript = document.getElementById("transcript");
  const form = document.getElementById("composer");
  const input = document.getElementById("user-input");
  const chips = document.getElementById("chips");
  const status = document.getElementById("status");
  const SESSION_KEY = "lumen-session-id";

  const sessionId = localStorage.getItem(SESSION_KEY) || crypto.randomUUID();
  localStorage.setItem(SESSION_KEY, sessionId);

  const history = [];
  let mode = "on-device";

  function renderMarkdownLite(text) {
    const escaped = text
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;");
    return escaped
      .replaceAll(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      .replaceAll(/`(.+?)`/g, "<code>$1</code>");
  }

  function addMessage(role, content) {
    const el = document.createElement("div");
    el.className = `msg ${role}`;
    el.setAttribute("role", "listitem");
    const meta = document.createElement("span");
    meta.className = "meta";
    meta.textContent = role === "user" ? "You" : "Lumen";
    const body = document.createElement("div");
    body.innerHTML = renderMarkdownLite(content);
    el.append(meta, body);
    transcript.appendChild(el);
    transcript.scrollTop = transcript.scrollHeight;
  }

  function setChips(items) {
    chips.replaceChildren();
    for (const label of items) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "chip";
      btn.textContent = label;
      btn.addEventListener("click", () => send(label));
      chips.appendChild(btn);
    }
  }

  function typing(on) {
    const existing = document.getElementById("typing");
    if (existing) existing.remove();
    if (!on) return;
    const el = document.createElement("div");
    el.id = "typing";
    el.className = "msg assistant";
    el.innerHTML = `<span class="meta">Lumen</span><span class="typing" aria-label="Thinking"><i></i><i></i><i></i></span>`;
    transcript.appendChild(el);
    transcript.scrollTop = transcript.scrollHeight;
  }

  async function detectApi() {
    try {
      const res = await fetch("/api/health", { headers: { Accept: "application/json" } });
      if (res.ok) {
        mode = "api";
        status.textContent = "Live API · FastAPI";
        return;
      }
    } catch {
      /* static host */
    }
    mode = "on-device";
    status.textContent = "On-device · GitHub Pages ready";
  }

  async function ask(message) {
    if (mode === "api") {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, session_id: sessionId, history }),
      });
      if (!res.ok) throw new Error("api");
      return res.json();
    }
    return window.LumenEngine.replyFor(message, sessionId);
  }

  async function send(raw) {
    const message = (raw ?? input.value).trim();
    if (!message) return;
    input.value = "";
    addMessage("user", message);
    history.push({ role: "user", content: message });
    typing(true);
    try {
      const result = await ask(message);
      typing(false);
      addMessage("assistant", result.reply);
      history.push({ role: "assistant", content: result.reply });
      if (history.length > 24) history.splice(0, history.length - 24);
      setChips(result.suggestions || []);
    } catch {
      typing(false);
      const fallback = window.LumenEngine.replyFor(message, sessionId);
      addMessage("assistant", fallback.reply);
      setChips(fallback.suggestions || []);
    }
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    send();
  });

  document.getElementById("clear-chat")?.addEventListener("click", () => {
    transcript.replaceChildren();
    history.length = 0;
    addMessage("assistant", "Fresh thread. What should we work on?");
    setChips(["What can you do?", "How were you built?", "72 F to C"]);
  });

  document.getElementById("export-chat")?.addEventListener("click", () => {
    const blob = new Blob(
      [history.map((m) => `${m.role}: ${m.content}`).join("\n\n")],
      { type: "text/plain" },
    );
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "lumen-transcript.txt";
    a.click();
    URL.revokeObjectURL(url);
  });

  addMessage(
    "assistant",
    "Welcome. I’m Lumen — a private assistant that runs in this page. Ask for help, try the chips, or inspect how I’m built.",
  );
  setChips(["What can you do?", "Give me an interview tip", "How were you built?"]);
  detectApi();
})();
