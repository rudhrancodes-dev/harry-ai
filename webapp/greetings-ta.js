// Tamil greeting pool for Rudhran, parallel to greetings.js.
// Same time-bucketed structure. The selector in greetings-bilingual.js
// picks an EN or TA line based on backend language config.

window.HARRY_GREETINGS_TA = (function () {
  const NAME = "ருத்ரன்";

  const dawn = [
    `காலை வணக்கம், ${NAME}.`,
    `சூரியனுக்கு முன்பே எழுந்துவிட்டீர்களா, ${NAME}?`,
    `அமைதியான நேரம், ${NAME}. உலகம் இன்னும் தூங்குகிறது.`,
    `வெகு சீக்கிரம் தொடங்கினீர்கள். மரியாதை, ${NAME}.`,
    `முதல் ஒளி. எங்கிருந்து தொடங்கலாம், ${NAME}?`,
  ];

  const morning = [
    `காலை வணக்கம், ${NAME}.`,
    `தயாராக உள்ளேன், ${NAME}.`,
    `மீண்டும் வருக, ${NAME}.`,
    `உங்கள் சேவையில், ${NAME}.`,
    `${NAME}, என்ன செய்யலாம் இன்று?`,
    `ஒரு அழகான நாள், ${NAME} — கட்டுவதற்கு.`,
    `${NAME}, நான் கேட்கிறேன்.`,
  ];

  const midday = [
    `மீண்டும் வருக, ${NAME}.`,
    `மதிய வணக்கம், ${NAME}.`,
    `${NAME}, எங்கு நிறுத்தினோம்?`,
    `${NAME}, தொடரலாம் என்றால்.`,
    `சரியான நேரத்தில் வந்தீர்கள், ${NAME}.`,
    `${NAME}, தொடங்குவோமா?`,
  ];

  const evening = [
    `மாலை வணக்கம், ${NAME}.`,
    `நீண்ட நாளா, ${NAME}?`,
    `${NAME}, விளக்குகள் மங்கின. நானும் மெதுவாக.`,
    `சாயங்காலம், ${NAME}. என்ன சிந்திக்கிறீர்கள்?`,
    `${NAME}, இரவு உணவு காத்திருக்கட்டும். உங்கள் தேவை என்ன?`,
    `${NAME}, இந்த நாளை நேர்த்தியாக முடிப்போம்.`,
  ];

  const night = [
    `நள்ளிரவு எண்ணெய் எரிக்கிறீர்களா, ${NAME}?`,
    `தாமதமான நேரம் உங்களுக்கு பொருந்துகிறது, ${NAME}.`,
    `${NAME}. நகரம் தூங்குகிறது. நாம் தூங்க வேண்டாம்.`,
    `${NAME}, நான் இங்கேயே இருக்கிறேன். எப்போதும்.`,
    `${NAME}, கிசுகிசுத்தாலும் கேட்கிறேன்.`,
    `${NAME}. இரவு காவலில், நான்.`,
  ];

  const flavor = [
    `${NAME}. ஏதாவது நல்லது செய்வோம்.`,
    `${NAME}, உங்கள் முறை.`,
    `${NAME}, தெளிவாக சிந்திக்க தயாரா?`,
    `${NAME}, ஒரு படி, ஒரு படியாக.`,
    `${NAME}, என்னை சொல்லுங்கள் — என்ன தீர்க்க வேண்டும்?`,
  ];

  function bucket(hour) {
    if (hour >= 4 && hour < 7) return "dawn";
    if (hour >= 7 && hour < 12) return "morning";
    if (hour >= 12 && hour < 17) return "midday";
    if (hour >= 17 && hour < 21) return "evening";
    return "night";
  }

  const pools = { dawn, morning, midday, evening, night, flavor };
  const all = [];
  for (const k of Object.keys(pools))
    for (const g of pools[k]) if (!all.includes(g)) all.push(g);

  function pick(seed) {
    const hr = new Date().getHours();
    const b = bucket(hr);
    const r = ((seed ?? Math.random()) * 100) | 0;
    const pool = r < 85 ? pools[b] : flavor;
    return pool[Math.floor(Math.random() * pool.length)];
  }

  return { pick, all, pools, NAME, bucket };
})();
