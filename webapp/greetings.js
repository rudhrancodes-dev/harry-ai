// Personalized greeting pool for Rudhran.
// Indexed by time-of-day buckets and mood. Picked deterministically by date so
// the same morning shows the same greeting until refresh, but you'll see new
// ones across the week — closer to how Claude's home greetings cycle.

window.HARRY_GREETINGS = (function () {
  const NAME = "Rudhran";

  const dawn = [
    `Good morning, ${NAME}.`,
    `Up before the sun, ${NAME}?`,
    `Quiet hours, ${NAME}. The world's still asleep.`,
    `Early start. I admire it, ${NAME}.`,
    `The kettle's metaphorical, but consider it on.`,
    `First light. Where shall we begin, ${NAME}?`,
    `Morning, ${NAME}. Inbox quiet. Coast clear.`,
  ];

  const morning = [
    `Good morning, ${NAME}.`,
    `Ready when you are, ${NAME}.`,
    `Morning, ${NAME}. What's on the docket?`,
    `Welcome back, ${NAME}.`,
    `At your service, ${NAME}.`,
    `Pleasure to see you again, ${NAME}.`,
    `Top of the morning, ${NAME}.`,
    `${NAME}. A fine day for building things.`,
    `Coffee or cold start, ${NAME}?`,
    `Morning. Eight new commits since you left.`,
    `Standing by, ${NAME}.`,
    `${NAME}, you have my attention.`,
  ];

  const midday = [
    `Welcome back, ${NAME}.`,
    `Hello again, ${NAME}.`,
    `Afternoon, ${NAME}. Ready to continue?`,
    `${NAME}. Where were we?`,
    `Picking up where we left off, ${NAME}?`,
    `${NAME}, the floor is yours.`,
    `Right on time, ${NAME}.`,
    `${NAME}, ready when you are.`,
    `${NAME}. Shall we?`,
    `Good afternoon, ${NAME}.`,
    `Listening, ${NAME}.`,
  ];

  const evening = [
    `Good evening, ${NAME}.`,
    `Evening, ${NAME}. Long day?`,
    `Welcome back, ${NAME}.`,
    `${NAME}. The lights are low. So am I.`,
    `Easy does it, ${NAME}.`,
    `Evening, ${NAME}. What's on your mind?`,
    `${NAME}, dinner can wait. What do you need?`,
    `Sunset shift, ${NAME}. I'm all yours.`,
    `${NAME}, let's wrap the day cleanly.`,
    `Good evening. Two unread, one urgent.`,
  ];

  const night = [
    `Burning the midnight oil, ${NAME}?`,
    `Late hours suit you, ${NAME}.`,
    `${NAME}. Quiet on the western front.`,
    `Still here, ${NAME}. Always.`,
    `Night shift, ${NAME}. What can I help with?`,
    `${NAME}, the city's asleep. We don't have to be.`,
    `Welcome back, ${NAME}. Don't tell anyone I noticed the hour.`,
    `${NAME}. Whisper if you'd like.`,
    `Standing watch, ${NAME}.`,
    `${NAME}, I'll be brief — and so should you, perhaps.`,
  ];

  // Mood / context flavors — drawn occasionally regardless of time
  const flavor = [
    `${NAME}. Let's make something good.`,
    `Ready to think clearly, ${NAME}?`,
    `${NAME}, the world is small and the work is large. Begin.`,
    `One step at a time, ${NAME}.`,
    `${NAME}, your move.`,
    `I've been thinking, ${NAME}.`,
    `${NAME}. Less talk, more progress?`,
    `Curious what we'll build today, ${NAME}.`,
    `${NAME}, the boring parts are handled. Focus on the interesting ones.`,
    `What needs solving, ${NAME}?`,
    `${NAME}. Tell me what good looks like.`,
    `${NAME}, the agenda is yours.`,
    `Brief and bright, ${NAME} — or long and slow. Your call.`,
    `${NAME}. I've been quiet. Productively so.`,
    `One small task or a tall mountain, ${NAME}?`,
  ];

  // Returning user / streak vibes
  const familiar = [
    `Back so soon, ${NAME}?`,
    `${NAME}. Round two.`,
    `Didn't expect you yet, ${NAME}. Pleasant surprise.`,
    `${NAME}. Right where we left off.`,
    `${NAME}, the kettle's still on, metaphorically.`,
  ];

  function bucket(hour) {
    if (hour >= 4 && hour < 7) return "dawn";
    if (hour >= 7 && hour < 12) return "morning";
    if (hour >= 12 && hour < 17) return "midday";
    if (hour >= 17 && hour < 21) return "evening";
    return "night";
  }

  const pools = { dawn, morning, midday, evening, night, flavor, familiar };

  // Build a flat catalog (deduped) for browsing in settings — "memory" feel
  const all = [];
  for (const k of Object.keys(pools)) {
    for (const g of pools[k]) {
      if (!all.includes(g)) all.push(g);
    }
  }

  function pick(seed) {
    const d = new Date();
    const hr = d.getHours();
    const b = bucket(hr);
    // Mix 80% time-of-day pool, 15% flavor, 5% familiar
    const r = ((seed ?? Math.random()) * 100) | 0;
    let pool;
    if (r < 80) pool = pools[b];
    else if (r < 95) pool = flavor;
    else pool = familiar;
    return pool[Math.floor(Math.random() * pool.length)];
  }

  return { pick, all, pools, NAME, bucket };
})();
