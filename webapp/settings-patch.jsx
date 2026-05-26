// settings-patch.jsx — non-invasive enhancement of the Settings drawer.
// Reads /api/config, renders a brain-backend dropdown + language toggle
// + voice-enrollment status as a portal injected into .settings when it
// becomes visible. Does NOT modify app.jsx.

(function () {
  const { useEffect, useState } = React;

  function BrainSwitcher() {
    const [cfg, setCfg] = useState(null);
    const [saving, setSaving] = useState(false);

    useEffect(() => {
      fetch("/api/config").then(r => r.json()).then(setCfg).catch(() => {});
    }, []);

    if (!cfg) return null;

    function patch(p) {
      setSaving(true);
      fetch("/api/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(p),
      })
        .then(r => r.json())
        .then((next) => { setCfg(next); setSaving(false); })
        .catch(() => setSaving(false));
    }

    const cell = { display: "flex", justifyContent: "space-between",
                   alignItems: "center", gap: 12, padding: "10px 0",
                   borderTop: "1px solid var(--hair, rgba(20,18,28,0.10))" };
    const sel = { font: "inherit", color: "var(--ink, #14121c)",
                  background: "transparent", border: "1px solid var(--hair)",
                  borderRadius: 8, padding: "4px 8px", outline: "none" };

    return (
      <div style={{ marginTop: 18 }}>
        <div style={cell}>
          <span className="l">Brain backend</span>
          <select style={sel} value={cfg.brain}
            onChange={(e) => patch({ brain: e.target.value })}>
            <option value="claude-code">Claude Pro · CLI</option>
            <option value="openrouter">OpenRouter · DeepSeek V3</option>
            <option value="openai-compat">OpenAI-compatible (opencode / Ollama)</option>
            <option value="off">Off (deterministic only)</option>
          </select>
        </div>
        <div style={cell}>
          <span className="l">Language</span>
          <select style={sel} value={cfg.language}
            onChange={(e) => {
              patch({ language: e.target.value });
              if (window.HARRY_LANG) window.HARRY_LANG.set(e.target.value);
            }}>
            <option value="en">English only</option>
            <option value="ta">தமிழ் (Tamil) only</option>
            <option value="auto">Auto (EN + TA)</option>
          </select>
        </div>
        <div style={cell}>
          <span className="l">Speaker recognition</span>
          <span className="v" style={{ fontVariantNumeric: "tabular-nums" }}>
            {cfg.speaker_enrolled
              ? `Enrolled · threshold ${cfg.speaker_threshold ?? 0.78}`
              : "Not enrolled · run python -m harry.enroll"}
          </span>
        </div>
        <div style={cell}>
          <span className="l">Memory vault</span>
          <span className="v">{cfg.vault_path || "—"}</span>
        </div>
        <div style={{ ...cell, color: "var(--ink-3)", fontSize: 12 }}>
          <span>Backend</span>
          <span>{saving ? "saving…" : (window.HARRY && window.HARRY.isConnected())
            ? "connected" : "offline preview"}</span>
        </div>
      </div>
    );
  }

  // Inject into the .settings drawer whenever it appears in the DOM.
  // The drawer mounts/unmounts on open/close, so we observe and re-inject.
  function tryInject() {
    const drawer = document.querySelector(".settings");
    if (!drawer || drawer.dataset.harryPatched === "1") return;
    drawer.dataset.harryPatched = "1";
    const host = document.createElement("div");
    host.className = "harry-brain-switcher";
    drawer.appendChild(host);
    ReactDOM.createRoot(host).render(<BrainSwitcher />);
  }

  const obs = new MutationObserver(tryInject);
  obs.observe(document.body, { childList: true, subtree: true });
  tryInject();
})();
