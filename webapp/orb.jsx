// orb.jsx — the Jarvis-meets-Apple iridescent sphere with glyph rings + particles

const { useEffect, useRef, useState, useMemo } = React;

// ── Glyph alphabet: a mix of mathematical / runic / latin / devanagari chars
//    that read as "alien tech" without committing to any one script.
const GLYPHS = "·∴∇∞∆◊◈◉◎⌬⍟⌖∀∃∂∰⊕⊗⊙⊚⨀⨁⌬⍙⎔⏣◇◈◧◨ⵘⵠⵙⵡξψφλΦΨΘΩꙮ𓂀𓏤𓊃𓉓ᚱᚳᛟᛇᛞᛏᛉ";
const TICKS_OUTER = 96;
const TICKS_INNER = 48;

function buildGlyphRingText(count, seed = 0) {
  let s = "";
  for (let i = 0; i < count; i++) {
    const c = GLYPHS[(i * 7 + seed) % GLYPHS.length];
    s += c + " ";
  }
  return s.trim();
}

function GlyphRings({ size = 520, state = "idle" }) {
  // Three concentric SVG rings: tick-marks (outer), glyph text (mid), dotted (inner)
  const r1 = 250; // outer ticks
  const r2 = 200; // glyph ring
  const r3 = 168; // dotted ring
  const r4 = 156; // segments arc

  const ticks = useMemo(() => {
    const arr = [];
    for (let i = 0; i < TICKS_OUTER; i++) {
      const a = (i / TICKS_OUTER) * Math.PI * 2;
      const major = i % 8 === 0;
      const len = major ? 12 : 5;
      const x1 = Math.cos(a) * r1;
      const y1 = Math.sin(a) * r1;
      const x2 = Math.cos(a) * (r1 - len);
      const y2 = Math.sin(a) * (r1 - len);
      arr.push({ x1, y1, x2, y2, major, i });
    }
    return arr;
  }, []);

  const innerDots = useMemo(() => {
    const arr = [];
    for (let i = 0; i < TICKS_INNER; i++) {
      const a = (i / TICKS_INNER) * Math.PI * 2;
      arr.push({ x: Math.cos(a) * r3, y: Math.sin(a) * r3 });
    }
    return arr;
  }, []);

  // Glyph ring uses textPath on a circle
  const glyphText = useMemo(() => buildGlyphRingText(64), []);
  const glyphTextInner = useMemo(() => buildGlyphRingText(48, 11), []);

  return (
    <div className="orb-rings" aria-hidden="true">
      <svg viewBox={`-${size / 2} -${size / 2} ${size} ${size}`}>
        <defs>
          <path id="glyphPath" d={`M ${-r2} 0 a ${r2} ${r2} 0 1 1 ${r2 * 2} 0 a ${r2} ${r2} 0 1 1 ${-r2 * 2} 0`} />
          <path id="glyphPathInner" d={`M ${-r4} 0 a ${r4} ${r4} 0 1 1 ${r4 * 2} 0 a ${r4} ${r4} 0 1 1 ${-r4 * 2} 0`} />
          <radialGradient id="haloGrad" cx="0.5" cy="0.5" r="0.5">
            <stop offset="60%" stopColor="rgba(255,255,255,0)" />
            <stop offset="100%" stopColor="currentColor" stopOpacity="0.18" />
          </radialGradient>
        </defs>

        {/* Outer tick ring */}
        <g className="ring-spin-slow">
          <circle cx="0" cy="0" r={r1} fill="none" stroke="currentColor" strokeOpacity="0.18" strokeWidth="0.5" />
          {ticks.map((t, i) => (
            <line
              key={i}
              x1={t.x1} y1={t.y1} x2={t.x2} y2={t.y2}
              stroke="currentColor"
              strokeOpacity={t.major ? 0.7 : 0.28}
              strokeWidth={t.major ? 1.1 : 0.55}
              strokeLinecap="round"
            />
          ))}
          {/* Four cardinal labels */}
          {["N", "E", "S", "W"].map((dir, i) => {
            const a = (i / 4) * Math.PI * 2 - Math.PI / 2;
            const x = Math.cos(a) * (r1 + 18);
            const y = Math.sin(a) * (r1 + 18);
            return (
              <text
                key={dir}
                x={x} y={y}
                textAnchor="middle"
                dominantBaseline="central"
                fontFamily="var(--font-mono)"
                fontSize="9"
                letterSpacing="2"
                fill="currentColor"
                fillOpacity="0.45"
              >{dir}</text>
            );
          })}
        </g>

        {/* Glyph text ring (outer) */}
        <g className="ring-spin-med">
          <text fontFamily="var(--font-mono)" fontSize="12" fill="currentColor" fillOpacity="0.65" letterSpacing="2">
            <textPath href="#glyphPath" startOffset="0">{glyphText}</textPath>
          </text>
        </g>

        {/* Arc segments (Jarvis-style) */}
        <g className="ring-spin-fast">
          {[0, 1, 2, 3].map((k) => {
            const start = (k / 4) * 360 + 6;
            const end = start + 78;
            const rad = (deg) => (deg * Math.PI) / 180;
            const x1 = Math.cos(rad(start)) * r4;
            const y1 = Math.sin(rad(start)) * r4;
            const x2 = Math.cos(rad(end)) * r4;
            const y2 = Math.sin(rad(end)) * r4;
            const large = end - start > 180 ? 1 : 0;
            return (
              <path
                key={k}
                d={`M ${x1} ${y1} A ${r4} ${r4} 0 ${large} 1 ${x2} ${y2}`}
                fill="none"
                stroke="currentColor"
                strokeOpacity="0.45"
                strokeWidth="1.2"
                strokeLinecap="round"
              />
            );
          })}
          {/* tiny diamond markers between segments */}
          {[0, 1, 2, 3].map((k) => {
            const a = (k / 4) * Math.PI * 2;
            const x = Math.cos(a) * r4;
            const y = Math.sin(a) * r4;
            return <rect key={k} x={x - 2} y={y - 2} width="4" height="4" transform={`rotate(45 ${x} ${y})`} fill="currentColor" fillOpacity="0.7" />;
          })}
        </g>

        {/* Inner glyph ring (smaller, counter-rotates) */}
        <g className="ring-spin-med" style={{ animationDirection: "normal", animationDuration: "22s" }}>
          <text fontFamily="var(--font-mono)" fontSize="9" fill="currentColor" fillOpacity="0.5" letterSpacing="2">
            <textPath href="#glyphPathInner" startOffset="0">{glyphTextInner}</textPath>
          </text>
        </g>

        {/* Dotted ring */}
        <g className="ring-spin-slow" style={{ animationDuration: "90s" }}>
          {innerDots.map((d, i) => (
            <circle key={i} cx={d.x} cy={d.y} r={i % 6 === 0 ? 1.5 : 0.8} fill="currentColor" fillOpacity={i % 6 === 0 ? 0.7 : 0.32} />
          ))}
        </g>

        {/* Thinking state overlay — extra rotating dashed ring */}
        {state === "thinking" && (
          <g>
            <circle cx="0" cy="0" r="232" fill="none" stroke="currentColor" strokeOpacity="0.4" strokeWidth="1.2" strokeDasharray="2 8" className="ring-spin-fast" />
            <circle cx="0" cy="0" r="218" fill="none" stroke="currentColor" strokeOpacity="0.6" strokeWidth="1.2" strokeDasharray="14 6" className="ring-spin-med" />
          </g>
        )}

        {/* Speaking state — radiating ripples */}
        {state === "speaking" && [0, 1, 2].map(i => (
          <circle key={i} cx="0" cy="0" r={150} fill="none" stroke="currentColor" strokeOpacity="0.5" strokeWidth="1.2" style={{
            animation: `ripple 1.6s ${i * 0.45}s cubic-bezier(.2,.7,.2,1) infinite`,
            transformOrigin: "0 0"
          }} />
        ))}
      </svg>
      <style>{`
        @keyframes ripple { 0% { r: 150; opacity: 0.8 } 100% { r: 245; opacity: 0 } }
      `}</style>
    </div>
  );
}

// Waveform-rings variant — concentric audio bars driven by amp
function WaveformRings({ amp, state }) {
  const N = 5;
  return (
    <div className="wave-rings" aria-hidden="true">
      {Array.from({ length: N }).map((_, i) => {
        const base = 90 + i * 36;
        const scale = 1 + amp * (0.06 + i * 0.04) * (state === "speaking" ? 1.6 : 1);
        return (
          <div key={i} className="wr" style={{
            width: base * 2 + "px",
            height: base * 2 + "px",
            opacity: 0.85 - i * 0.13,
            transform: `translate(-50%, -50%) scale(${scale.toFixed(3)})`,
            transition: "transform 80ms linear",
            borderColor: `color-mix(in oklab, var(--iri-${(i % 6) + 1}) 85%, transparent)`,
            borderWidth: (1.5 + i * 0.4) + "px",
          }} />
        );
      })}
    </div>
  );
}

// Floating particles around the orb
function Particles({ amp, intensity = 1, state }) {
  const ref = useRef(null);
  useEffect(() => {
    const c = ref.current;
    if (!c) return;
    const ctx = c.getContext("2d");
    let raf;
    let w, h, dpr;
    function resize() {
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      const rect = c.getBoundingClientRect();
      w = c.width = rect.width * dpr;
      h = c.height = rect.height * dpr;
    }
    resize();
    window.addEventListener("resize", resize);
    const N = 90;
    const parts = Array.from({ length: N }).map(() => ({
      a: Math.random() * Math.PI * 2,
      r: 160 + Math.random() * 240,
      s: 0.0003 + Math.random() * 0.0015,
      sz: 0.4 + Math.random() * 1.4,
      hue: Math.random(),
      drift: (Math.random() - 0.5) * 0.4,
    }));
    function loop() {
      const cx = w / 2, cy = h / 2;
      ctx.clearRect(0, 0, w, h);
      const amplitude = ampRef.current;
      for (const p of parts) {
        const speedBoost = state === "thinking" ? 4 : state === "speaking" ? 2.5 : state === "listening" ? 1.8 : 1;
        p.a += p.s * speedBoost;
        const rr = p.r + Math.sin(p.a * 3) * 6 + amplitude * 30 * (1 + p.drift);
        const x = cx + Math.cos(p.a) * rr * dpr;
        const y = cy + Math.sin(p.a) * rr * dpr;
        ctx.beginPath();
        ctx.arc(x, y, p.sz * dpr * (1 + amplitude * 0.6), 0, Math.PI * 2);
        const colors = ["#ffb7d6", "#c8a6ff", "#a5c8ff", "#bff0d5", "#ffd2b8", "#ffe8a3"];
        ctx.fillStyle = colors[Math.floor(p.hue * colors.length)];
        ctx.globalAlpha = (0.25 + amplitude * 0.5) * intensity;
        ctx.fill();
      }
      ctx.globalAlpha = 1;
      raf = requestAnimationFrame(loop);
    }
    loop();
    return () => { cancelAnimationFrame(raf); window.removeEventListener("resize", resize); };
  }, [intensity, state]);

  // amp via ref so we don't restart the loop
  const ampRef = useRef(amp);
  useEffect(() => { ampRef.current = amp; }, [amp]);

  return <div className="particles"><canvas ref={ref} /></div>;
}

// ── Jarvis particle sphere — dense 3D point cloud, voice-reactive ────
function JarvisSphere({ amp, state, mouseRef }) {
  const ref = useRef(null);
  const ampRef = useRef(amp);
  const stateRef = useRef(state);
  useEffect(() => { ampRef.current = amp; }, [amp]);
  useEffect(() => { stateRef.current = state; }, [state]);

  useEffect(() => {
    const c = ref.current;
    if (!c) return;
    const ctx = c.getContext("2d");
    let raf;
    let w, h, dpr;
    function resize() {
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      const r = c.getBoundingClientRect();
      w = c.width = r.width * dpr;
      h = c.height = r.height * dpr;
    }
    resize();
    window.addEventListener("resize", resize);

    // Build particle distributions
    const N_SHELL = 2600;
    const shell = [];
    for (let i = 0; i < N_SHELL; i++) {
      // Fibonacci sphere
      const phi = Math.acos(-1 + (2 * i) / N_SHELL);
      const theta = Math.sqrt(N_SHELL * Math.PI) * phi;
      shell.push({
        x: Math.sin(phi) * Math.cos(theta),
        y: Math.cos(phi),
        z: Math.sin(phi) * Math.sin(theta),
        n: 0.84 + Math.random() * 0.34,          // radial jitter
        size: 0.6 + Math.pow(Math.random(), 2) * 2.4,
        hue: Math.random(),                       // for color variance
        spark: Math.random() < 0.06 ? 1 : 0,      // a few bright sparks
        phase: Math.random() * Math.PI * 2,
      });
    }
    // Inner volume
    const N_INNER = 700;
    const inner = [];
    for (let i = 0; i < N_INNER; i++) {
      const r = Math.pow(Math.random(), 0.55) * 0.95;
      const phi = Math.acos(2 * Math.random() - 1);
      const theta = Math.random() * Math.PI * 2;
      inner.push({
        x: r * Math.sin(phi) * Math.cos(theta),
        y: r * Math.cos(phi),
        z: r * Math.sin(phi) * Math.sin(theta),
        r,
        size: 0.5 + Math.random() * 1.2,
        phase: Math.random() * Math.PI * 2,
      });
    }
    // Radial filaments (a few bright streaks)
    const N_FIL = 36;
    const filaments = [];
    for (let i = 0; i < N_FIL; i++) {
      const phi = Math.acos(2 * Math.random() - 1);
      const theta = Math.random() * Math.PI * 2;
      filaments.push({
        x: Math.sin(phi) * Math.cos(theta),
        y: Math.cos(phi),
        z: Math.sin(phi) * Math.sin(theta),
        len: 0.18 + Math.random() * 0.25,
      });
    }

    let yaw = 0, pitch = 0.05, t = 0;

    function loop() {
      t += 0.016;
      const ampV = ampRef.current;
      const st = stateRef.current;

      const speedY = ({
        idle: 0.0035,
        wake: 0.006,
        listening: 0.0055,
        thinking: 0.013,
        speaking: 0.008,
        muted: 0.001,
        tool: 0.011,
      })[st] || 0.0035;
      yaw += speedY;

      // Mouse parallax
      const mx = mouseRef?.current?.x ?? 0;
      const my = mouseRef?.current?.y ?? 0;
      pitch = my * 0.5 + Math.sin(t * 0.15) * 0.08;
      const yawOffset = mx * 0.6;

      const cosY = Math.cos(yaw + yawOffset), sinY = Math.sin(yaw + yawOffset);
      const cosX = Math.cos(pitch), sinX = Math.sin(pitch);

      ctx.clearRect(0, 0, w, h);
      const cx = w / 2, cy = h / 2;
      const baseR = Math.min(w, h) * 0.32;

      // Atmospheric core glow
      const coreA = 0.22 + (ampV - 1) * 1.6 + (st === "speaking" ? 0.08 : 0);
      const g1 = ctx.createRadialGradient(cx, cy, 0, cx, cy, baseR * 1.4);
      g1.addColorStop(0, `rgba(255,210,140,${Math.max(0, coreA * 0.5)})`);
      g1.addColorStop(0.35, `rgba(255,140,40,${Math.max(0, coreA * 0.18)})`);
      g1.addColorStop(1, "rgba(0,0,0,0)");
      ctx.fillStyle = g1;
      ctx.fillRect(0, 0, w, h);

      // Outer halo
      const g2 = ctx.createRadialGradient(cx, cy, baseR * 0.9, cx, cy, baseR * 2);
      g2.addColorStop(0, "rgba(255,120,30,0.08)");
      g2.addColorStop(1, "rgba(0,0,0,0)");
      ctx.fillStyle = g2;
      ctx.fillRect(0, 0, w, h);

      ctx.globalCompositeOperation = "lighter";

      // Wave that travels through the sphere (speaking) or expansion (listening)
      const speakWave = st === "speaking" ? 0.07 : 0;
      const listenJitter = st === "listening" ? 0.04 * Math.max(0, ampV - 1) * 30 : 0;
      const thinkContract = st === "thinking" ? -0.02 : 0;

      function project(px, py, pz, scale) {
        const x = px * scale;
        const y = py * scale;
        const z = pz * scale;
        const xr = x * cosY - z * sinY;
        const zr = x * sinY + z * cosY;
        const yr = y * cosX - zr * sinX;
        const zr2 = y * sinX + zr * cosX;
        const persp = 1 / (1 + zr2 / scale * 0.45);
        return {
          sx: cx + xr * persp,
          sy: cy + yr * persp,
          sz: zr2,
          persp,
        };
      }

      // 1. Inner volume (deep core points)
      for (const p of inner) {
        const breath = 1 + Math.sin(t * 1.4 + p.phase) * 0.015 + speakWave * Math.sin(t * 5 - p.r * 6) * 0.4;
        const scale = baseR * breath * (1 + (ampV - 1) * 0.3 + thinkContract);
        const { sx, sy, sz, persp } = project(p.x, p.y, p.z, scale);
        const a = (sz / baseR + 1) * 0.5;
        const alpha = a * 0.4 * persp;
        const r = 255;
        const gr = Math.floor(120 + a * 80 + p.r * 40);
        const b = Math.floor(20 + a * 50);
        ctx.fillStyle = `rgba(${r},${gr},${b},${alpha})`;
        const sz2 = p.size * dpr * (0.6 + a * 0.5);
        ctx.fillRect(sx - sz2 / 2, sy - sz2 / 2, sz2, sz2);
      }

      // 2. Shell points
      for (const p of shell) {
        const ripple = speakWave * Math.sin(t * 5 + (p.x + p.y + p.z) * 4) * 0.6;
        const jitter = listenJitter * (Math.sin(p.phase + t * 8) * 0.04 + (Math.random() - 0.5) * 0.025);
        const radial = p.n + ripple + jitter + thinkContract * 0.5;
        const breath = 1 + (ampV - 1) * 0.6;
        const scale = baseR * radial * breath;
        const { sx, sy, sz, persp } = project(p.x, p.y, p.z, scale);
        const a = (sz / baseR + 1) * 0.5;  // 0=back, 1=front
        const sparkBoost = p.spark ? (0.5 + Math.sin(t * 3 + p.phase) * 0.5) : 0;
        const alpha = (0.22 + a * 0.78) * persp + sparkBoost * 0.4;
        const r = 255;
        const gr = Math.floor(100 + a * 140 + sparkBoost * 80);
        const b = Math.floor(15 + a * 90 + sparkBoost * 60);
        const size = p.size * dpr * (0.55 + a * 0.9) + sparkBoost * dpr;
        ctx.fillStyle = `rgba(${r},${Math.min(255, gr)},${Math.min(255, b)},${alpha})`;
        ctx.fillRect(sx - size / 2, sy - size / 2, size, size);
      }

      // 3. Bright radial filaments (only on front hemisphere)
      ctx.lineWidth = 0.7 * dpr;
      for (const f of filaments) {
        const scale = baseR * (1 + (ampV - 1) * 0.6);
        const p1 = project(f.x * (1 - f.len), f.y * (1 - f.len), f.z * (1 - f.len), scale);
        const p2 = project(f.x, f.y, f.z, scale);
        if (p2.sz < 0) continue;
        const a = (p2.sz / baseR + 1) * 0.5;
        const grad = ctx.createLinearGradient(p1.sx, p1.sy, p2.sx, p2.sy);
        grad.addColorStop(0, `rgba(255,220,160,${0.0})`);
        grad.addColorStop(1, `rgba(255,200,120,${0.7 * a})`);
        ctx.strokeStyle = grad;
        ctx.beginPath();
        ctx.moveTo(p1.sx, p1.sy);
        ctx.lineTo(p2.sx, p2.sy);
        ctx.stroke();
      }

      // Bright hot spots — extra bright on speaking peaks
      if (st === "speaking" || st === "wake") {
        for (let i = 0; i < 8; i++) {
          const a = (i / 8 + t * 0.1) * Math.PI * 2;
          const rr = baseR * (0.85 + Math.sin(t * 4 + i) * 0.08);
          const x = cx + Math.cos(a) * rr;
          const y = cy + Math.sin(a) * rr * 0.7;
          const grd = ctx.createRadialGradient(x, y, 0, x, y, 22 * dpr);
          grd.addColorStop(0, "rgba(255,220,160,0.7)");
          grd.addColorStop(1, "rgba(255,120,40,0)");
          ctx.fillStyle = grd;
          ctx.fillRect(x - 22 * dpr, y - 22 * dpr, 44 * dpr, 44 * dpr);
        }
      }

      ctx.globalCompositeOperation = "source-over";
      raf = requestAnimationFrame(loop);
    }
    loop();
    return () => { cancelAnimationFrame(raf); window.removeEventListener("resize", resize); };
  }, []); // mount-only; ampRef / stateRef provide live data

  return <canvas ref={ref} className="jarvis-canvas" />;
}

// ── Jarvis HUD frame — corner brackets, tick ring, mono labels ───────
function JarvisFrame({ state, size = 640 }) {
  const s = size;
  const m = 8;
  const armLen = 56;
  const armLen2 = 28;
  const corner = (cx, cy, fx, fy, key) => (
    <g key={key} opacity="0.85">
      <line x1={cx} y1={cy} x2={cx + armLen * fx} y2={cy} stroke="currentColor" strokeWidth="1.4" />
      <line x1={cx} y1={cy} x2={cx} y2={cy + armLen * fy} stroke="currentColor" strokeWidth="1.4" />
      <line x1={cx + 14 * fx} y1={cy + 4 * fy} x2={cx + (armLen2 + 14) * fx} y2={cy + 4 * fy} stroke="currentColor" strokeWidth="0.8" opacity="0.55" />
      <line x1={cx + 4 * fx} y1={cy + 14 * fy} x2={cx + 4 * fx} y2={cy + (armLen2 + 14) * fy} stroke="currentColor" strokeWidth="0.8" opacity="0.55" />
      <line x1={cx + 26 * fx} y1={cy + 4 * fy} x2={cx + 4 * fx} y2={cy + 26 * fy} stroke="currentColor" strokeWidth="0.55" opacity="0.4" />
      <rect x={cx + (fx > 0 ? 0 : -3)} y={cy + (fy > 0 ? 0 : -3)} width="3" height="3" fill="currentColor" />
    </g>
  );

  const ticks = [];
  for (let i = 0; i < 60; i++) {
    const a = (i / 60) * Math.PI * 2;
    const major = i % 5 === 0;
    const r1 = s / 2 - 22;
    const r2 = r1 - (major ? 10 : 4);
    const x1 = s / 2 + Math.cos(a) * r1;
    const y1 = s / 2 + Math.sin(a) * r1;
    const x2 = s / 2 + Math.cos(a) * r2;
    const y2 = s / 2 + Math.sin(a) * r2;
    ticks.push(<line key={i} x1={x1} y1={y1} x2={x2} y2={y2} stroke="currentColor" strokeWidth="0.55" opacity={major ? 0.55 : 0.22} />);
  }

  return (
    <div className="jarvis-frame">
      <svg viewBox={`0 0 ${s} ${s}`}>
        {/* Outer dashed ring */}
        <circle cx={s / 2} cy={s / 2} r={s / 2 - 8} fill="none" stroke="currentColor" strokeWidth="0.5" opacity="0.18" strokeDasharray="1 6" />
        <circle cx={s / 2} cy={s / 2} r={s / 2 - 24} fill="none" stroke="currentColor" strokeWidth="0.4" opacity="0.14" />

        {/* Tick ring */}
        <g className="jv-ring-rot">{ticks}</g>

        {/* Inner arc segments (4 quadrants, with breaks) */}
        <g opacity="0.55">
          {[0, 1, 2, 3].map((k) => {
            const r = s / 2 - 56;
            const start = (k / 4) * 360 + 22;
            const end = start + 46;
            const rad = (d) => (d * Math.PI) / 180;
            const x1 = s / 2 + Math.cos(rad(start)) * r;
            const y1 = s / 2 + Math.sin(rad(start)) * r;
            const x2 = s / 2 + Math.cos(rad(end)) * r;
            const y2 = s / 2 + Math.sin(rad(end)) * r;
            return <path key={k} d={`M ${x1} ${y1} A ${r} ${r} 0 0 1 ${x2} ${y2}`} fill="none" stroke="currentColor" strokeWidth="1" />;
          })}
        </g>

        {/* Corner brackets */}
        {corner(m, m, 1, 1, "tl")}
        {corner(s - m, m, -1, 1, "tr")}
        {corner(m, s - m, 1, -1, "bl")}
        {corner(s - m, s - m, -1, -1, "br")}

        {/* Crosshair */}
        <g opacity="0.55">
          <line x1={s / 2 - 18} y1={s / 2} x2={s / 2 - 8} y2={s / 2} stroke="currentColor" strokeWidth="0.7" />
          <line x1={s / 2 + 8} y1={s / 2} x2={s / 2 + 18} y2={s / 2} stroke="currentColor" strokeWidth="0.7" />
          <line x1={s / 2} y1={s / 2 - 18} x2={s / 2} y2={s / 2 - 8} stroke="currentColor" strokeWidth="0.7" />
          <line x1={s / 2} y1={s / 2 + 8} x2={s / 2} y2={s / 2 + 18} stroke="currentColor" strokeWidth="0.7" />
        </g>

        {/* Top label bar */}
        <g opacity="0.7">
          <line x1={s / 2 - 64} y1={32} x2={s / 2 - 26} y2={32} stroke="currentColor" strokeWidth="0.6" />
          <line x1={s / 2 + 26} y1={32} x2={s / 2 + 64} y2={32} stroke="currentColor" strokeWidth="0.6" />
          <text x={s / 2} y={36} textAnchor="middle" fontFamily="var(--font-mono)" fontSize="8.5" letterSpacing="3" fill="currentColor">JV-01 // NEURAL CORE</text>
        </g>
        <g opacity="0.55">
          <text x={s / 2} y={s - 28} textAnchor="middle" fontFamily="var(--font-mono)" fontSize="7.5" letterSpacing="2.6" fill="currentColor">
            {`STATE :: ${(state || "idle").toUpperCase()}    INTEGRITY 98.4%    SYNC ✓`}
          </text>
        </g>
      </svg>
      <div className="jv-labels">
        <span className="tl">JV-01<br />CORE</span>
        <span className="tr">AUDIO ▸ IN<br />48k · 24b</span>
        <span className="bl">42.36°N · 71.05°W<br />UPLINK ✓</span>
        <span className="br">NEURAL · 04<br />T-CYCLE 0.012s</span>
      </div>
    </div>
  );
}

// Compose: rings + core + particles + waveform variant
function Orb({ state, style, amp, intensity }) {
  return (
    <div className="orb-wrap" data-style={style}>
      {style !== "waveform" && <GlyphRings state={state} />}
      {style === "waveform" ? <WaveformRings amp={amp} state={state} /> : <div className="orb-core" />}
    </div>
  );
}

Object.assign(window, { Orb, GlyphRings, WaveformRings, Particles, JarvisSphere, JarvisFrame });
