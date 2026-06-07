const VIC_HOLIDAYS = {
  '06-08': { open: [10, 0], close: [17, 0], label: "King's Birthday" },
  '04-18': { open: [10, 0], close: [17, 0], label: 'Good Friday' },
  '04-20': { open: [10, 0], close: [17, 0], label: 'Easter Sunday' },
  '04-21': { open: [10, 0], close: [17, 0], label: 'Easter Monday' },
  '01-26': { open: [10, 0], close: [17, 0], label: 'Australia Day' },
  '01-01': { open: [10, 0], close: [17, 0], label: "New Year's Day" },
  '12-25': { open: [10, 0], close: [17, 0], label: 'Christmas Day' },
  '12-26': { open: [10, 0], close: [17, 0], label: 'Boxing Day' },
};

const DAYS = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'];

function parseHours(raw) {
  const dayMap = { sunday: 0, monday: 1, tuesday: 2, wednesday: 3, thursday: 4, friday: 5, saturday: 6 };
  const re = /(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)(?:\s+to\s+(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday))?\s+(\d{1,2}:\d{2}(?:am|pm))\s*[-–]\s*(\d{1,2}:\d{2}(?:am|pm))/gi;

  const slots = [];
  let m;
  while ((m = re.exec(raw)) !== null) {
    slots.push({
      start: m[1].toLowerCase(),
      end: (m[2] || m[1]).toLowerCase(),
      open: m[3],
      close: m[4],
    });
  }

  function parseHm(s) {
    s = s.trim().toLowerCase();
    const isPm = s.endsWith('pm');
    s = s.replace('am', '').replace('pm', '').trim();
    let [h, m] = s.split(':').map(Number);
    if (isPm && h !== 12) h += 12;
    if (!isPm && h === 12) h = 0;
    return [h, m];
  }

  return DAYS.map((name, i) => {
    for (const s of slots) {
      if (dayMap[s.start] <= i && i <= dayMap[s.end]) {
        return { day: name[0].toUpperCase() + name.slice(1), open: parseHm(s.open), close: parseHm(s.close), hours: `${s.open} – ${s.close}` };
      }
    }
    return null;
  });
}

function getHoliday() {
  const now = new Date();
  const key = String(now.getMonth() + 1).padStart(2, '0') + '-' + String(now.getDate()).padStart(2, '0');
  return VIC_HOLIDAYS[key] || null;
}

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  res.setHeader('Cache-Control', 'public, s-maxage=3600, stale-while-revalidate=600');

  if (req.method === 'OPTIONS') return res.status(200).end();

  try {
    const r = await fetch('https://www.chadstone.com.au/', {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/120.0.0.0 Mobile Safari/537.36',
      },
    });
    if (!r.ok) throw new Error(`upstream ${r.status}`);
    const html = await r.text();
    const m = html.match(/"openingHours"\s*:\s*"([^"]+)"/);
    if (!m) throw new Error('Could not find openingHours in JSON-LD');

    const weekly = parseHours(m[1]);
    const holiday = getHoliday();

    res.status(200).json({ weekly, holiday, cache_hint: 'scraped' });
  } catch (e) {
    const fallback = [
      { day: 'Sunday', open: [10, 0], close: [19, 0], hours: '10:00 am – 7:00 pm' },
      { day: 'Monday', open: [9, 0], close: [17, 30], hours: '9:00 am – 5:30 pm' },
      { day: 'Tuesday', open: [9, 0], close: [17, 30], hours: '9:00 am – 5:30 pm' },
      { day: 'Wednesday', open: [9, 0], close: [17, 30], hours: '9:00 am – 5:30 pm' },
      { day: 'Thursday', open: [9, 0], close: [21, 0], hours: '9:00 am – 9:00 pm' },
      { day: 'Friday', open: [9, 0], close: [21, 0], hours: '9:00 am – 9:00 pm' },
      { day: 'Saturday', open: [9, 0], close: [21, 0], hours: '9:00 am – 9:00 pm' },
    ];
    res.status(200).json({ weekly: fallback, holiday: null, error: e.message, using_fallback: true });
  }
}
