// harry-bridge.js — connects the UI's auto state machine to the real
// Python backend over a WebSocket. The original app.jsx demo cycle keeps
// running as a graceful fallback when the backend isn't reachable.
//
// Backend protocol (JSON over ws://HOST/ws):
//   server → client:
//     { type:"state",      state:"idle|wake|listening|thinking|tool|speaking|muted" }
//     { type:"transcript", who:"user|harry", text:"..." }
//     { type:"tool",       name:"...", arg:"...", done:false }
//     { type:"greeting",   text:"..." }
//   client → server:
//     { type:"wake" }          // user pressed space / clicked orb
//     { type:"mute",  on:bool }
//     { type:"text",  text:"..." } // typed input fallback if mic disabled
//     { type:"config", patch:{ HARRY_BRAIN:"openrouter", ... } }

(function () {
  const proto = location.protocol === "https:" ? "wss:" : "ws:";
  const url = `${proto}//${location.host}/ws`;
  let ws = null;
  let connected = false;
  const listeners = new Set();

  function emit(msg) {
    listeners.forEach((fn) => {
      try { fn(msg); } catch (_) { /* ignore */ }
    });
  }

  function connect() {
    try { ws = new WebSocket(url); }
    catch (_) { setTimeout(connect, 2000); return; }
    ws.onopen = () => { connected = true; emit({ type: "connection", on: true }); };
    ws.onclose = () => {
      connected = false;
      emit({ type: "connection", on: false });
      setTimeout(connect, 2000);
    };
    ws.onerror = () => { try { ws.close(); } catch (_) {} };
    ws.onmessage = (ev) => {
      let m; try { m = JSON.parse(ev.data); } catch (_) { return; }
      emit(m);
    };
  }
  connect();

  window.HARRY = {
    on(fn) { listeners.add(fn); return () => listeners.delete(fn); },
    send(msg) {
      if (connected && ws && ws.readyState === 1) {
        ws.send(JSON.stringify(msg));
        return true;
      }
      return false;
    },
    isConnected: () => connected,
    wake() { return this.send({ type: "wake" }); },
    mute(on) { return this.send({ type: "mute", on: !!on }); },
    text(t) { return this.send({ type: "text", text: t }); },
    setConfig(patch) { return this.send({ type: "config", patch }); },
  };
})();
