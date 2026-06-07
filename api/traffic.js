export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  res.setHeader('Cache-Control', 'public, s-maxage=60, stale-while-revalidate=30');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  const url = new URL(req.url, `http://${req.headers.host || 'localhost'}`);
  let startDate = url.searchParams.get('startDate');
  if (!startDate) {
    const d = new Date();
    startDate = d.toISOString().slice(0, 10);
  }

  try {
    const r = await fetch(`https://www.chadstone.com.au/api/traffic?startDate=${startDate}`, {
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
    res.status(502).json({ error: 'Traffic data unavailable', detail: e.message });
  }
}
