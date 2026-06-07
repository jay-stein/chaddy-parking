export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  res.setHeader('Cache-Control', 'public, s-maxage=30, stale-while-revalidate=15');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  try {
    const r = await fetch('https://www.chadstone.com.au/api/parking', {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/120.0.0.0 Mobile Safari/537.36',
        'Accept': 'application/json',
        'Referer': 'https://www.chadstone.com.au/directions/parking',
      },
    });
    if (!r.ok) throw new Error(`upstream ${r.status}`);
    const data = await r.json();
    res.status(200).json(data);
  } catch (e) {
    res.status(502).json({ error: 'Parking data unavailable', detail: e.message });
  }
}
