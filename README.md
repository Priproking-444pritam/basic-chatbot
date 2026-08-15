# Lumen

**A privacy-first conversational assistant you can ship as a website.**

Lumen started as a four-rule Python chatbot. It is now a product-shaped portfolio piece: a distinctive UI, a testable intent engine, a FastAPI backend, Docker, CI, and a GitHub Pages site that works **without an API key**.

[Live demo (this repo)](https://priproking-444pritam.github.io/basic-chatbot/) · [Architecture](#architecture) · [Deploy the website](#create-the-website)

---

## Why this exists

Most “chatbot” repos are a `while True` loop and an unstyled form. That doesn’t match how assistants are built now:

- People expect a **real interface**, not a tutorial page.
- Demos die when a free server sleeps — so the **site must run on-device**.
- Interviewers probe **safety** (`eval`, XSS, crisis copy) and **tradeoffs** (rules vs LLMs).
- You should be able to **add a model later** without rewriting the product.

Lumen is the smallest honest version of that.

## What it does

| Capability | How |
| --- | --- |
| Live website + chat | Static `index.html` + `assets/engine.js` |
| Math & unit conversion | Safe expression walker (Python) / constrained eval (JS) |
| Time, notes, interview & study coaching | Scored intents |
| Optional LLM | FastAPI adapter to any OpenAI-compatible API |
| CLI | `python chatbot.py` |
| Tests | `pytest` on engine, API, and unsafe-eval rejection |

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python chatbot.py "hello"
uvicorn app.main:app --reload --port 8000
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). The page talks to `/api/chat` when the server is up, and falls back to the in-browser engine otherwise.

```bash
pytest -q
docker compose up --build
```

## Create the website

You do **not** need a backend to put this on the internet.

1. Push this repository to GitHub (already done if you’re looking at it).
2. **Settings → Pages → Build and deployment**
   - Source: **Deploy from a branch**
   - Branch: `main` / root (`/`)
3. Wait a minute. The site is:
   `https://<your-username>.github.io/basic-chatbot/`
4. Optional: add a custom domain in the same Pages settings.

That’s the version you send in applications. It loads fast, looks finished, and chat works on a phone.

### Optional: hosted API + LLM

Use this when you want open-ended answers for unknown intents.

```bash
export LLM_API_KEY=sk-...          # OpenAI, Groq, Together, etc.
export LLM_BASE_URL=https://api.openai.com/v1
export LLM_MODEL=gpt-4o-mini
docker compose up --build
```

Unknown questions then route to the model. Everything the engine already handles stays deterministic and tested.

| Host | Notes |
| --- | --- |
| GitHub Pages | Static site (recommended for the demo link) |
| Render / Railway / Fly | Run the Docker image; set `CORS_ORIGINS` to your Pages URL |
| Vercel / Netlify | Serve the static files; point chat at the API if you have one |

## Architecture

```
browser
  ├─ assets/app.js          UI, a11y, XSS-safe rendering, API detect
  └─ assets/engine.js       On-device intents (GitHub Pages)

FastAPI (optional)
  ├─ POST /api/chat         Pydantic validation, session id
  ├─ GET  /api/health
  └─ app/engine.py          Same behaviors as JS, plus LLM adapter
        └─ app/tools.py     math, units, clocks — no raw eval()
```

**Design choices worth talking about in interviews**

1. **Hybrid intelligence.** Rules for things that must be right (math, conversions). Models for the long tail. The demo never hard-depends on a vendor.
2. **Two runtimes, one product.** JS for zero-ops hosting; Python for tests, CLI, and production.
3. **Safety.** User HTML is escaped. Python math walks an AST and rejects names. Wellbeing replies refuse to play therapist and point to real help (988 in the US).
4. **Honest UX.** If Lumen can’t do it, it says so and offers chips — it doesn’t hallucinate a fake brain.

## Project layout

```
app/                 FastAPI + Python engine
assets/              CSS, JS engine, favicon
tests/               pytest
index.html           Marketing site + live chat
chatbot.py           Terminal client
Dockerfile           Production server
.github/workflows    CI
```

## Environment

| Variable | Default | Purpose |
| --- | --- | --- |
| `LLM_API_KEY` | empty | Enables LLM fallback |
| `LLM_BASE_URL` | `https://api.openai.com/v1` | Compatible providers |
| `LLM_MODEL` | `gpt-4o-mini` | Model id |
| `CORS_ORIGINS` | `*` | Comma-separated allowlist |

## API

`POST /api/chat`

```json
{
  "message": "convert 72 F to C",
  "session_id": "optional",
  "history": []
}
```

```json
{
  "reply": "72 F → **22.22 C**",
  "intent": "convert",
  "source": "engine",
  "suggestions": ["100 km to mi"],
  "session_id": "…"
}
```

## What to say in an interview

- “I turned a toy chatbot into a **shippable assistant** with a real site.”
- “The interesting part isn’t the LLM — it’s **product boundaries**: what runs on-device, what is tested, and when a model is actually worth calling.”
- “I treated UX as part of the system: suggestion chips, export, reduced motion, and copy that doesn’t overclaim.”

Then open the live demo and type `how were you built?`

## License

MIT
