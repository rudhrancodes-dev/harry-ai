// Bilingual selector that wraps greetings.js (EN) + greetings-ta.js (TA).
// Reads the backend's /api/config once on load to learn the user's language
// preference, then delegates pick() to the right pool.
//
// Falls back to English if the Tamil pool isn't loaded or the fetch fails.

(function () {
  const EN = window.HARRY_GREETINGS;
  const TA = window.HARRY_GREETINGS_TA;
  if (!EN) return; // nothing to wrap — bail rather than crash the page

  // Capture the ORIGINAL pick before monkey-patching so the new pick can
  // delegate to it without recursing into itself.
  const originalEnPick = EN.pick.bind(EN);

  let lang = "en";          // "en" | "ta" | "auto"
  let nameOverride = null;

  fetch("/api/config")
    .then((r) => r.ok ? r.json() : null)
    .then((cfg) => {
      if (!cfg) return;
      if (cfg.language) lang = cfg.language;
      if (cfg.user_name) nameOverride = cfg.user_name;
    })
    .catch(() => { /* offline static preview is fine */ });

  function pickLang() {
    if (lang === "ta") return "ta";
    if (lang === "en") return "en";
    // auto: alternate by hour bucket parity for variety
    return new Date().getHours() % 2 ? "ta" : "en";
  }

  function pickGreeting(seed) {
    if (pickLang() === "ta" && TA) return TA.pick(seed);
    return originalEnPick(seed);
  }

  const originalAll = EN.all.slice();
  EN.pick = pickGreeting;
  EN.all = originalAll.concat(TA ? TA.all : []);

  window.HARRY_LANG = {
    current: () => lang,
    set: (v) => { lang = v; },
  };
})();
