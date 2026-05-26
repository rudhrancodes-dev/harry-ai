// app.jsx — Harry AI main shell

const { useEffect, useRef, useState, useMemo, useCallback } = React;

// ── Tweak defaults (persisted via host) ───────────────────────────────
const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "theme": "solaris",
  "orbStyle": "jarvis",
  "state": "auto",
  "showTranscript": false,
  "showAgent": true,
  "bgIntensity": 0.55,
  "voiceReactive": true,
  "draggable": true
}/*EDITMODE-END*/;

// ── Demo "voice" simulator — composes sines + noise to drive amp ─────
function useAmplitude(state, enabled) {
  const [amp, setAmp] = useState(1);
  useEffect(() => {
    if (!enabled) { setAmp(1); return; }
    let raf, t = 0;
    function loop() {
      t += 0.016;
      let target;
      if (state === "listening") {
        // user speaking sim: dense, jittery
        target = 1 + 0.06 * Math.sin(t * 4.7) + 0.05 * Math.sin(t * 11.3) + 0.04 * (Math.random() - 0.5);
      } else if (state === "speaking") {
        // Harry speaking: structured cadence
        const phrase = Math.sin(t * 1.2);
        target = 1 + 0.05 + 0.07 * Math.abs(Math.sin(t * 5)) + 0.04 * Math.abs(phrase);
      } else if (state === "thinking") {
        target = 1 - 0.04 + 0.02 * Math.sin(t * 1.8);
      } else if (state === "wake") {
        target = 1.06 + 0.02 * Math.sin(t * 9);
      } else if (state === "muted") {
        target = 0.96;
      } else {
        target = 1 + 0.012 * Math.sin(t * 0.7);
      }
      setAmp(target);
      raf = requestAnimationFrame(loop);
    }
    loop();
    return () => cancelAnimationFrame(raf);
  }, [state, enabled]);
  return amp;
}

// ── Simulated transcript / agent narrative ───────────────────────────
const DEMO_SCRIPT = [
  // User → Harry → tools → Harry
  {
    user: "Harry, summarise the engineering sync from yesterday, then draft a status update for the team.",
    tools: [
      { name: "memory.search", arg: 'channel:#eng-sync date:yesterday', dur: 700 },
      { name: "calendar.fetch", arg: "Eng Sync — Tue 4PM", dur: 600 },
      { name: "notion.read", arg: "Eng Sync notes — 5 pages", dur: 1100 },
      { name: "drafts.create", arg: "Weekly Status — Wk 22", dur: 900 },
    ],
    response: "Three threads stood out, Rudhran. Vector store rollout slipped two days — Priya needs a sign-off on the index shape. Onboarding ARR is up 18 percent week-over-week, and the iOS push regression is fixed in build 412. I've drafted the status note; it's in your queue under \"Weekly Status — Wk 22\".",
  },
  {
    user: "Book a 30 minute slot with Priya tomorrow, mid-afternoon, and send her the rollout doc.",
    tools: [
      { name: "calendar.findSlot", arg: "Priya · tomorrow · 14–16", dur: 600 },
      { name: "calendar.book", arg: "Vector store sign-off · 15:00", dur: 500 },
      { name: "drive.share", arg: "Vector Store Rollout v3", dur: 600 },
    ],
    response: "Booked for 3 PM. She has the doc with comment access. I held a 15-minute buffer either side, in case it runs long.",
  },
  {
    user: "Play me something calm. And dim the studio lights to forty percent.",
    tools: [
      { name: "spotify.play", arg: 'playlist: "Late Evenings"', dur: 400 },
      { name: "home.lights", arg: "studio · 40%", dur: 300 },
    ],
    response: "Done. Lights at forty. I queued the slower half of the playlist — let me know if it drifts.",
  },
];

// One "live" caption renderer that types out word by word
function useLiveText(text, enabled, speedMs = 38) {
  const [shown, setShown] = useState("");
  useEffect(() => {
    if (!enabled) { setShown(text); return; }
    setShown("");
    let i = 0;
    const id = setInterval(() => {
      i++;
      setShown(text.slice(0, i));
      if (i >= text.length) clearInterval(id);
    }, speedMs);
    return () => clearInterval(id);
  }, [text, enabled, speedMs]);
  return shown;
}

// Format current time / day for top bar
function useClock() {
  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 30 * 1000);
    return () => clearInterval(id);
  }, []);
  const hh = String(now.getHours()).padStart(2, "0");
  const mm = String(now.getMinutes()).padStart(2, "0");
  const day = now.toLocaleDateString(undefined, { weekday: "short" }).toUpperCase();
  const dateStr = now.toLocaleDateString(undefined, { month: "short", day: "numeric" }).toUpperCase();
  return { hh, mm, day, dateStr };
}

// ── Top bar ──────────────────────────────────────────────────────────
function TopBar({ state }) {
  const { hh, mm, day, dateStr } = useClock();
  const stateLabel = ({
    idle: "STANDING BY",
    wake: "AWAKE",
    listening: "LISTENING",
    thinking: "THINKING",
    speaking: "SPEAKING",
    muted: "MUTED",
    tool: "WORKING",
  })[state] || "STANDING BY";
  return (
    <div className="topbar">
      <div className="wordmark">
        <span className="h">Harry</span>
        <span className="sub">Intelligence · v1.0</span>
      </div>
      <div className="statpill" data-state={state}>
        <span className="dot" />
        <span>{stateLabel}</span>
      </div>
      <div className="meta">
        <span>{day} · {dateStr}</span>
        <span className="sep" />
        <span style={{ fontVariantNumeric: "tabular-nums" }}>{hh}:{mm}</span>
        <span className="sep" />
        <span>NEURAL · 04</span>
      </div>
    </div>
  );
}

// ── Hints / keyboard shortcuts ───────────────────────────────────────
function Hints({ state, onSpace }) {
  return (
    <div className="hints">
      <div className="row"><span className="kbd">Space</span><span>Hold to talk</span></div>
      <div className="row"><span className="kbd">⌘</span><span className="kbd">M</span><span>Mute</span></div>
      <div className="row"><span className="kbd">⌘</span><span className="kbd">T</span><span>Transcript</span></div>
      <div className="row"><span className="kbd">Esc</span><span>Dismiss</span></div>
    </div>
  );
}

// ── Agent log (bottom-right) ─────────────────────────────────────────
function AgentLog({ items }) {
  if (!items?.length) return null;
  return (
    <div className="agentlog" aria-live="polite">
      {items.slice(-5).map((it, i) => (
        <div className="item" key={i}>
          <span className="tag">{it.name}</span>
          <span>·</span>
          <span style={{ color: "var(--ink-3)" }}>{it.arg}</span>
          {it.done && <span className="ok">✓</span>}
        </div>
      ))}
    </div>
  );
}

// ── Tool card (centre-bottom) ────────────────────────────────────────
function ToolCard({ active }) {
  if (!active) return null;
  return (
    <div className="tool-card">
      <span className="ico">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none"><path d="M12 2 L14 8 L20 8 L15 12 L17 18 L12 14 L7 18 L9 12 L4 8 L10 8 Z" fill="currentColor"/></svg>
      </span>
      <span>
        <span style={{ opacity: 0.6, marginRight: 8 }}>{active.name}</span>
        <span className="step">{active.arg}</span>
      </span>
      <span className="progress"><span /></span>
    </div>
  );
}

// ── Transcript drawer ────────────────────────────────────────────────
function Transcript({ open, turns, onClose }) {
  return (
    <aside className={"transcript-drawer" + (open ? " open" : "")} aria-hidden={!open}>
      <div className="td-hd">
        <div className="ttl">Today<small>Transcript · {turns.length} turns</small></div>
        <button className="icon-btn" onClick={onClose} aria-label="Close">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6"><path d="M6 6 L18 18 M18 6 L6 18"/></svg>
        </button>
      </div>
      <div className="td-body">
        {turns.map((t, i) => (
          <React.Fragment key={i}>
            {t.user && (
              <div className="turn user">
                <div className="who">Rudhran</div>
                <div className="what">{t.user}</div>
              </div>
            )}
            {t.response && (
              <div className="turn">
                <div className="who">Harry</div>
                <div className="what">"{t.response}"</div>
                {t.tools && t.tools.length > 0 && (
                  <div className="tools">
                    {t.tools.map((tt, j) => <span className="t" key={j}>{tt.name} · {tt.arg}</span>)}
                  </div>
                )}
              </div>
            )}
          </React.Fragment>
        ))}
      </div>
    </aside>
  );
}

// ── Settings (left drawer) ───────────────────────────────────────────
function Settings({ open, onClose }) {
  const G = window.HARRY_GREETINGS;
  return (
    <aside className={"settings" + (open ? " open" : "")} aria-hidden={!open}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <h4>Settings<small>Voice · Persona · Memory</small></h4>
        <button className="icon-btn" onClick={onClose} aria-label="Close">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6"><path d="M6 6 L18 18 M18 6 L6 18"/></svg>
        </button>
      </div>
      <div className="setting"><span className="l">Wake word</span><span className="v">"Hey Harry"</span></div>
      <div className="setting"><span className="l">Voice</span><span className="v">Butler · Calm (en-IN)</span></div>
      <div className="setting"><span className="l">Latency</span><span className="v">Edge · 120 ms median</span></div>
      <div className="setting"><span className="l">Privacy</span><span className="v">On-device wake · Cloud reasoning</span></div>
      <div className="setting">
        <span className="l">Greeting catalog · {G.all.length} variations</span>
        <div className="cat">
          {G.all.map((g, i) => <div key={i}>{g}</div>)}
        </div>
      </div>
    </aside>
  );
}

// ── Greeting / caption block above the orb ───────────────────────────
function CaptionBlock({ state, greeting, userText, harryText }) {
  if (state === "idle" || state === "wake" || state === "muted") {
    return (
      <div className="caption-wrap">
        <div className="greeting" key={greeting}>
          {greeting.split(/\b(Rudhran)\b/).map((part, i) =>
            part === "Rudhran"
              ? <span key={i} className="accent">{part}</span>
              : <span key={i}>{part}</span>
          )}
        </div>
        {state === "idle" && (
          <div className="caption" style={{ opacity: 0.6 }}>
            Say "Hey Harry" — or hold space.
          </div>
        )}
        {state === "wake" && (
          <div className="caption">I'm listening.</div>
        )}
        {state === "muted" && (
          <div className="caption" style={{ opacity: 0.7 }}>Muted. Tap the orb to wake me.</div>
        )}
      </div>
    );
  }
  if (state === "listening") {
    return (
      <div className="caption-wrap">
        <div className="caption">
          "{userText}<span className="partial">…</span>"
        </div>
      </div>
    );
  }
  if (state === "thinking") {
    return (
      <div className="caption-wrap">
        <div className="caption" style={{ opacity: 0.7 }}>One moment, Rudhran.</div>
      </div>
    );
  }
  if (state === "speaking" || state === "tool") {
    return (
      <div className="caption-wrap">
        <div className="caption">"{harryText}"</div>
      </div>
    );
  }
  return null;
}

// ── State pill below the orb ─────────────────────────────────────────
function StatePill({ state }) {
  const map = {
    idle: { label: "Standing by", icon: null },
    wake: { label: "Awake", icon: "dot" },
    listening: { label: "Listening", icon: "bars" },
    thinking: { label: "Thinking", icon: "spin" },
    speaking: { label: "Speaking", icon: "bars" },
    tool: { label: "Working", icon: "spin" },
    muted: { label: "Muted", icon: null },
  };
  const m = map[state] || map.idle;
  return (
    <div className="state-pill">
      {m.icon === "bars" && (
        <span className="mini-bars">
          <i /><i /><i /><i /><i />
        </span>
      )}
      {m.icon === "spin" && (
        <span className="glyph" style={{ width: 12, height: 12, borderRadius: "50%", background: "conic-gradient(from 0deg, var(--iri-2), var(--iri-3), var(--iri-4), var(--iri-2))", display: "inline-block", animation: "ring-spin 1.4s linear infinite" }} />
      )}
      <span>{m.label}</span>
    </div>
  );
}

// ── Tools cluster (right side) ───────────────────────────────────────
function ToolsCluster({ muted, onMute, transcriptOpen, onTranscript, onSettings }) {
  return (
    <div className="tools-cluster">
      <button className={"icon-btn" + (muted ? " active" : "")} onClick={onMute} title="Mute (⌘M)">
        {muted ? (
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6"><path d="M3 3 L21 21"/><path d="M9 9 v6 a3 3 0 0 0 6 0 v-3"/><path d="M15 5 a3 3 0 0 0 -6 0 v3"/></svg>
        ) : (
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6"><rect x="9" y="3" width="6" height="12" rx="3"/><path d="M5 11 a7 7 0 0 0 14 0"/><path d="M12 18 v3"/></svg>
        )}
      </button>
      <button className={"icon-btn" + (transcriptOpen ? " active" : "")} onClick={onTranscript} title="Transcript (⌘T)">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6"><path d="M4 6 h16 M4 10 h10 M4 14 h16 M4 18 h8"/></svg>
      </button>
      <button className="icon-btn" onClick={onSettings} title="Settings">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a7.97 7.97 0 0 0 .1-1.5l2-1.6-2-3.4-2.4.8a8 8 0 0 0-2.6-1.5L14 5h-4l-.5 2.8a8 8 0 0 0-2.6 1.5l-2.4-.8-2 3.4 2 1.6a8 8 0 0 0 0 3l-2 1.6 2 3.4 2.4-.8a8 8 0 0 0 2.6 1.5L10 21h4l.5-2.8a8 8 0 0 0 2.6-1.5l2.4.8 2-3.4z"/></svg>
      </button>
    </div>
  );
}

// ── Main app ─────────────────────────────────────────────────────────
function HarryApp() {
  const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);

  // State machine: idle → wake → listening → thinking → tool → speaking → idle
  const [autoState, setAutoState] = useState("idle");
  const state = t.state === "auto" ? autoState : t.state;

  const [muted, setMuted] = useState(false);
  const effectiveState = muted ? "muted" : state;

  const [transcriptOpen, setTranscriptOpen] = useState(t.showTranscript);
  useEffect(() => { setTranscriptOpen(t.showTranscript); }, [t.showTranscript]);

  const [settingsOpen, setSettingsOpen] = useState(false);

  // Greeting — chosen once on mount, persists this session
  const greeting = useMemo(() => window.HARRY_GREETINGS.pick(), []);

  // Demo conversation cycle
  const [turnIdx, setTurnIdx] = useState(0);
  const [activeTool, setActiveTool] = useState(null);
  const [agentItems, setAgentItems] = useState([]);
  const [turns, setTurns] = useState([]);

  const turn = DEMO_SCRIPT[turnIdx % DEMO_SCRIPT.length];

  // Drive auto state machine
  useEffect(() => {
    if (t.state !== "auto") return;
    if (muted) return;
    let timers = [];
    let cancelled = false;
    function run() {
      if (cancelled) return;
      setAutoState("idle");
      timers.push(setTimeout(() => {
        if (cancelled) return;
        setAutoState("wake");
        timers.push(setTimeout(() => {
          if (cancelled) return;
          setAutoState("listening");
          timers.push(setTimeout(() => {
            if (cancelled) return;
            setAutoState("thinking");
            // Run tool sequence
            let delay = 600;
            const toolsRan = [];
            (turn.tools || []).forEach((tl, idx) => {
              timers.push(setTimeout(() => {
                if (cancelled) return;
                setAutoState("tool");
                setActiveTool(tl);
                toolsRan.push(tl);
                setAgentItems(prev => [...prev, { ...tl }]);
              }, delay));
              delay += tl.dur;
              timers.push(setTimeout(() => {
                if (cancelled) return;
                setAgentItems(prev => prev.map((it, i) => i === prev.length - 1 ? { ...it, done: true } : it));
              }, delay - 100));
            });
            timers.push(setTimeout(() => {
              if (cancelled) return;
              setActiveTool(null);
              setAutoState("speaking");
              setTurns(prev => [...prev, { user: turn.user, response: turn.response, tools: toolsRan }]);
              // Wait for "speech" to finish
              const speakMs = Math.min(7800, 1800 + turn.response.length * 22);
              timers.push(setTimeout(() => {
                if (cancelled) return;
                setTurnIdx(i => i + 1);
                run();
              }, speakMs));
            }, delay + 300));
          }, 1800 + turn.user.length * 15));
        }, 700));
      }, 3200));
    }
    run();
    return () => {
      cancelled = true;
      timers.forEach(clearTimeout);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [turnIdx, t.state, muted]);

  // Voice-reactive amplitude
  const amp = useAmplitude(effectiveState, t.voiceReactive);

  // Live-type captions
  const userTyped = useLiveText(turn.user, effectiveState === "listening", 28);
  const harryTyped = useLiveText(turn.response, effectiveState === "speaking", 22);

  // Keyboard shortcuts
  useEffect(() => {
    function onKey(e) {
      if (e.key === " " && !e.repeat) { e.preventDefault(); /* simulate hold-to-talk: jump to listening */ }
      if ((e.metaKey || e.ctrlKey) && (e.key === "m" || e.key === "M")) { e.preventDefault(); setMuted(m => !m); }
      if ((e.metaKey || e.ctrlKey) && (e.key === "t" || e.key === "T")) { e.preventDefault(); setTranscriptOpen(o => !o); }
      if (e.key === "Escape") { setTranscriptOpen(false); setSettingsOpen(false); }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  // Drag orb
  const wrapRef = useRef(null);
  const [pos, setPos] = useState({ x: 0, y: 0 });
  const mouseRef = useRef({ x: 0, y: 0 });
  const dragging = useRef(false);
  const dragStart = useRef({ x: 0, y: 0 });
  function onPointerDown(e) {
    if (!t.draggable) return;
    if (e.target.closest("button")) return;
    dragging.current = true;
    dragStart.current = { x: e.clientX - pos.x, y: e.clientY - pos.y };
    wrapRef.current?.setPointerCapture(e.pointerId);
    wrapRef.current?.classList.add("dragging");
  }
  function onPointerMove(e) {
    // parallax for Jarvis sphere
    if (wrapRef.current) {
      const rect = wrapRef.current.getBoundingClientRect();
      mouseRef.current = {
        x: (e.clientX - (rect.left + rect.width / 2)) / rect.width,
        y: (e.clientY - (rect.top + rect.height / 2)) / rect.height,
      };
    }
    if (!dragging.current) return;
    setPos({ x: e.clientX - dragStart.current.x, y: e.clientY - dragStart.current.y });
  }
  function onPointerUp(e) {
    dragging.current = false;
    wrapRef.current?.classList.remove("dragging");
  }
  function onOrbClick(e) {
    if (Math.abs(e.clientX - dragStart.current.x - pos.x) > 4) return; // ignore drag end
    setMuted(m => !m);
  }

  // Apply theme + bg intensity at root
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", t.theme);
    document.documentElement.style.setProperty("--bg-intensity", t.bgIntensity);
  }, [t.theme, t.bgIntensity]);

  return (
    <div className="stage" data-state={effectiveState} data-transcript={transcriptOpen ? "true" : "false"} data-theme={t.theme} data-orbstyle={t.orbStyle}>
      <Particles amp={amp} intensity={t.bgIntensity * 1.6 + 0.4} state={effectiveState} />

      <TopBar state={effectiveState} />

      <div className="center" ref={wrapRef}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
      >
        <div style={{ transform: `translate(${pos.x}px, ${pos.y}px)`, transition: dragging.current ? "none" : "transform 600ms cubic-bezier(.2,.7,.2,1)" }}>
          <div
            className={"orb-wrap" + (muted ? " muted" : "")}
            data-style={t.orbStyle}
            style={{ "--amp": amp }}
            onClick={onOrbClick}
          >
            {t.orbStyle === "jarvis" && (
              <>
                <JarvisFrame state={effectiveState} />
                <JarvisSphere amp={amp} state={effectiveState} mouseRef={mouseRef} />
              </>
            )}
            {t.orbStyle === "waveform" && <WaveformRings amp={amp} state={effectiveState} />}
            {(t.orbStyle === "sphere" || t.orbStyle === "blob") && (
              <>
                <GlyphRings state={effectiveState} />
                <div className="orb-core" />
              </>
            )}
          </div>
        </div>
        <CaptionBlock state={effectiveState} greeting={greeting} userText={userTyped} harryText={harryTyped} />
        <div className="below-orb">
          <StatePill state={effectiveState} />
        </div>
      </div>

      <ToolCard active={t.showAgent ? activeTool : null} />

      <Hints />
      {t.showAgent && <AgentLog items={agentItems} />}

      <ToolsCluster
        muted={muted}
        onMute={() => setMuted(m => !m)}
        transcriptOpen={transcriptOpen}
        onTranscript={() => setTranscriptOpen(o => !o)}
        onSettings={() => setSettingsOpen(o => !o)}
      />

      <Transcript open={transcriptOpen} turns={turns} onClose={() => setTranscriptOpen(false)} />
      <Settings open={settingsOpen} onClose={() => setSettingsOpen(false)} />

      <TweaksPanel>
        <TweakSection label="Theme" />
        <TweakRadio label="Palette" value={t.theme}
          options={[
            { value: "iridescent", label: "Iridescent" },
            { value: "obsidian", label: "Obsidian" },
            { value: "solaris", label: "Solaris" },
          ]}
          onChange={(v) => setTweak("theme", v)} />
        <TweakSlider label="Background intensity" value={t.bgIntensity} min={0} max={1} step={0.05}
          onChange={(v) => setTweak("bgIntensity", v)} />

        <TweakSection label="Orb" />
        <TweakSelect label="Style" value={t.orbStyle}
          options={[
            { value: "jarvis", label: "Jarvis · Particle sphere" },
            { value: "sphere", label: "Iridescent sphere + rings" },
            { value: "blob", label: "Soft blob" },
            { value: "waveform", label: "Waveform rings" },
          ]}
          onChange={(v) => setTweak("orbStyle", v)} />
        <TweakToggle label="Voice-reactive" value={t.voiceReactive} onChange={(v) => setTweak("voiceReactive", v)} />
        <TweakToggle label="Draggable" value={t.draggable} onChange={(v) => setTweak("draggable", v)} />

        <TweakSection label="State" />
        <TweakSelect label="Force state" value={t.state}
          options={[
            { value: "auto", label: "Auto cycle (demo)" },
            { value: "idle", label: "Idle" },
            { value: "wake", label: "Wake" },
            { value: "listening", label: "Listening" },
            { value: "thinking", label: "Thinking" },
            { value: "speaking", label: "Speaking" },
            { value: "tool", label: "Tool / working" },
          ]}
          onChange={(v) => setTweak("state", v)} />

        <TweakSection label="HUD" />
        <TweakToggle label="Transcript drawer" value={t.showTranscript} onChange={(v) => setTweak("showTranscript", v)} />
        <TweakToggle label="Agent status + log" value={t.showAgent} onChange={(v) => setTweak("showAgent", v)} />
      </TweaksPanel>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<HarryApp />);
