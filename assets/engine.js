(() => {
  const notesBySession = new Map();

  const INTENTS = [
    ["greeting", /\b(hi|hello|hey|yo|good (morning|afternoon|evening))\b/i, 10],
    ["farewell", /\b(bye|goodbye|see you|later|exit|quit)\b/i, 10],
    ["thanks", /\b(thanks|thank you|appreciate|thx)\b/i, 8],
    ["identity", /\b(who are you|your name|what are you|about you)\b/i, 12],
    ["help", /\b(help|what can you do|capabilities|commands|features)\b/i, 12],
    ["time", /\b(time|date|today|day is it|clock)\b/i, 9],
    ["math", /[\d]+\s*[+\-*/^%]\s*[\d]+|calculate|compute|what(?:'s| is)\s+\d/i, 11],
    ["convert", /\bconvert\b|\d+\s*(km|mi|kg|lb|c|f|celsius|fahrenheit)\b/i, 11],
    ["interview", /\b(interview|resume|star method|behavioral|hiring)\b/i, 10],
    ["study", /\b(study|learn|focus|pomodoro|revise|exam)\b/i, 9],
    ["wellbeing", /\b(anxious|stressed|overwhelmed|sad|lonely|burnout)\b/i, 12],
    ["privacy", /\b(privacy|data|store|remember me|tracking)\b/i, 9],
    ["joke", /\b(joke|funny|make me laugh)\b/i, 8],
    ["note_add", /\b(remember|note|save this|add to notes)\b/i, 10],
    ["note_list", /\b(notes|what did i save|show notes)\b/i, 9],
    ["how_built", /\b(how (are you|were you) (built|made)|architecture|tech stack)\b/i, 11],
  ];

  const HELP = [
    "What can you do?",
    "Convert 72 F to C",
    "Interview tip for behavioral questions",
    "What time is it?",
  ];

  function classify(text) {
    let best = "unknown";
    let score = 0;
    for (const [name, pattern, weight] of INTENTS) {
      if (pattern.test(text) && weight > score) {
        best = name;
        score = weight;
      }
    }
    return best;
  }

  function safeEval(expr) {
    const cleaned = expr.replace(/\^/g, "**").replace(/[^0-9.+\-*/()%\s]/g, "");
    if (!cleaned.trim()) throw new Error("empty");
    // eslint-disable-next-line no-new-func
    const fn = new Function(`"use strict"; return (${cleaned});`);
    const value = fn();
    if (typeof value !== "number" || Number.isNaN(value)) throw new Error("nan");
    return value;
  }

  const LENGTH = { mm: 0.001, cm: 0.01, m: 1, km: 1000, in: 0.0254, inch: 0.0254, ft: 0.3048, mi: 1609.344 };
  const MASS = { mg: 0.001, g: 1, kg: 1000, lb: 453.59237, oz: 28.349523125 };

  function toC(v, u) {
    if (["c", "celsius"].includes(u)) return v;
    if (["f", "fahrenheit"].includes(u)) return ((v - 32) * 5) / 9;
    if (["k", "kelvin"].includes(u)) return v - 273.15;
    throw new Error("temp");
  }

  function fromC(v, u) {
    if (["c", "celsius"].includes(u)) return v;
    if (["f", "fahrenheit"].includes(u)) return (v * 9) / 5 + 32;
    if (["k", "kelvin"].includes(u)) return v + 273.15;
    throw new Error("temp");
  }

  function convert(value, src, dest) {
    const s = src.toLowerCase();
    const d = dest.toLowerCase();
    const temps = ["c", "f", "k", "celsius", "fahrenheit", "kelvin"];
    if (temps.includes(s) && temps.includes(d)) return fromC(toC(value, s), d);
    if (LENGTH[s] && LENGTH[d]) return (value * LENGTH[s]) / LENGTH[d];
    if (MASS[s] && MASS[d]) return (value * MASS[s]) / MASS[d];
    throw new Error(`Cannot convert ${src} to ${dest}`);
  }

  function replyFor(message, sessionId = "web") {
    const text = String(message || "").trim();
    if (!text) {
      return { reply: "Say something and I’ll meet you there.", intent: "empty", suggestions: HELP.slice(0, 3), source: "engine" };
    }
    const intent = classify(text);
    const notes = notesBySession.get(sessionId) || [];
    notesBySession.set(sessionId, notes);

    const handlers = {
      greeting: () => ({
        reply:
          "Hey — I’m Lumen. I can help with math, conversions, study focus, interview prep, and quick notes. What’s on your mind?",
        suggestions: ["What can you do?", "Give me an interview tip", "12 * 17.5"],
      }),
      farewell: () => ({
        reply: "Take care. I’ll be here when you need a second brain.",
        suggestions: ["Start a new topic"],
      }),
      thanks: () => ({ reply: "Anytime. Want to keep going?", suggestions: ["Show my notes"] }),
      identity: () => ({
        reply:
          "I’m Lumen, a conversational assistant designed to run in the browser or on a small FastAPI backend. I start on-device so you can ship a real demo without an API key.",
        suggestions: ["How were you built?", "What about privacy?"],
      }),
      help: () => ({
        reply:
          "Here’s what I’m good at right now:\n• Math and unit conversions\n• Time and date\n• Session notes (remember this…)\n• Interview and study coaching\n• Honest answers about privacy and how I’m built",
        suggestions: HELP,
      }),
      time: () => {
        const now = new Date();
        return {
          reply: `It’s ${now.toLocaleString(undefined, { weekday: "long", dateStyle: "long", timeStyle: "short" })}.`,
          suggestions: ["What can you do?"],
        };
      },
      math: () => {
        try {
          const expr = text.replace(/[^0-9.+\-*/^()%\s]/g, " ").replace(/\s+/g, " ").trim();
          const value = safeEval(expr);
          const pretty = Number.isInteger(value) ? String(value) : String(Number(value.toPrecision(6)));
          return { reply: `${expr} = **${pretty}**`, suggestions: ["Convert 5 km to mi"] };
        } catch {
          return { reply: "I can evaluate expressions like `12 * (4 + 3)` or `2^10`.", suggestions: ["2^10"] };
        }
      },
      convert: () => {
        const match = text.replaceAll("°", "").match(/(?:convert\s+)?(-?\d+(?:\.\d+)?)\s*([a-z]+)\s+(?:to|in)\s+([a-z]+)/i);
        if (!match) return { reply: "Try: convert 72 F to C, or 5 km to mi.", suggestions: ["72 F to C"] };
        try {
          const out = convert(Number(match[1]), match[2], match[3]);
          return { reply: `${match[1]} ${match[2]} → **${Number(out.toPrecision(4))} ${match[3]}**`, suggestions: ["100 km to mi"] };
        } catch (err) {
          return { reply: String(err.message || err), suggestions: ["72 F to C"] };
        }
      },
      interview: () => ({
        reply:
          "For behavioral interviews, use STAR and keep it tight:\n1. **Situation** — one sentence of context\n2. **Task** — what you owned\n3. **Action** — what *you* did\n4. **Result** — a number if you have one\n\nPractice: “Tell me about a time you shipped under ambiguity.”",
        suggestions: ["How were you built?", "Study focus tip"],
      }),
      study: () => ({
        reply:
          "Use a 50/10 focus block: 50 minutes on one outcome, 10 minutes away from the screen. Write the outcome as a verb (“finish the API tests”), not a vibe.",
        suggestions: ["Interview tip"],
      }),
      wellbeing: () => ({
        reply:
          "That’s heavy, and you don’t have to carry it alone. I’m a software assistant, not a clinician. If you’re in crisis, contact local emergency services. In the US, call or text **988**.",
        suggestions: ["Study focus tip"],
      }),
      privacy: () => ({
        reply:
          "Default mode is on-device: messages stay in this browser tab unless you deploy the API. Optional LLM keys are a switch you control — not a requirement.",
        suggestions: ["How were you built?"],
      }),
      joke: () => ({
        reply: "Why did the frontend refuse to argue with the API? It didn’t want a cross-origin relationship.",
        suggestions: ["Interview tip"],
      }),
      note_add: () => {
        const payload = text
          .replace(/^(please\s+)?(remember|note|save this|add to notes)\s*(that\s+|this\s*:?\s*)?/i, "")
          .replace(/[ .]+$/, "");
        if (!payload) return { reply: "Tell me what to remember. Example: remember this: ship the README.", suggestions: [] };
        notes.push(payload);
        return { reply: `Saved (${notes.length}): ${payload}`, suggestions: ["Show my notes"] };
      },
      note_list: () => {
        if (!notes.length) return { reply: "No notes in this session yet. Say “remember this: …” to add one.", suggestions: [] };
        return { reply: `Session notes:\n${notes.map((n, i) => `${i + 1}. ${n}`).join("\n")}`, suggestions: [] };
      },
      how_built: () => ({
        reply:
          "Lumen is a hybrid assistant:\n• A scored intent engine for reliable, testable answers\n• Safe math and unit conversion\n• FastAPI for optional LLM completion\n• This page runs the same engine in JavaScript so GitHub Pages works with zero servers",
        suggestions: ["What about privacy?"],
      }),
    };

    const run = handlers[intent] || (() => ({
      reply: `I heard “${text.slice(0, 80)}.” I don’t improvise long answers unless an LLM key is connected. I can help with math, conversions, notes, and interview prep.`,
      suggestions: HELP,
    }));
    const out = run();
    return { reply: out.reply, intent: handlers[intent] ? intent : "unknown", suggestions: out.suggestions || [], source: "engine" };
  }

  window.LumenEngine = { replyFor, classify };
})();
