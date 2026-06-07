# Jay Chaddy Parking Guide — Plan

## App Structure

4-tab PWA (Progressive Web App) installed via Chrome "Add to Home Screen".

| Tab | Data | Source |
|---|---|---|
| Finder | Live car park A-F occupancy | `/api/parking` |
| Planner | 7-day hourly traffic forecast + bar chart | `/api/traffic` |
| Hours | Centre trading hours, precinct hours | `/api/hours` (scrapes JSON-LD from homepage) |
| Map | Chadstone parking map image | `images/chaddy_map.png` |

## API Endpoints

| Endpoint | Method | Source |
|---|---|---|
| `/api/parking` | GET | `https://www.chadstone.com.au/api/parking` |
| `/api/traffic` | GET | `https://www.chadstone.com.au/api/traffic?startDate=...` |
| `/api/hours` | GET | Scrapes `openingHours` from JSON-LD on Chadstone homepage + VIC holiday lookup |

## Current Issue

### Problem
The Python proxy (`server.py`) gets **403 Forbidden** when forwarding requests to
`chadstone.com.au/api/parking` and `/api/traffic`. Direct `curl` requests work fine.

### Root Cause
Chadstone's API blocks Python's `urllib` regardless of headers sent.
`curl.exe` works because it uses a different TLS stack / HTTP implementation.

### Fix (applied)
Replaced `urllib.request` calls with `subprocess.run(['curl.exe', ...])` in
`server.py`. Curl sends the right TLS handshake and headers that Chadstone accepts.

## Dev Server Startup

**CORRECT way to start (from PowerShell):**
```powershell
Start-Process -FilePath python -ArgumentList server.py -WorkingDirectory "path\to\chadstone" -WindowStyle Hidden
```

**DO NOT use `-RedirectStandardOutput` or `-RedirectStandardError`** — these cause the
server to hang at startup (stdout pipe deadlock).

**DO NOT use `-NoNewWindow`** with bash/shell tools — the process attaches to the
parent console, which the tool can't interact with.

### Restart Procedure

1. Kill ALL Python processes first:
```powershell
Get-Process python | Stop-Process -Force
```

2. Wait for port 8000 to release (TIME_WAIT can linger for 30-120s):
```powershell
while (Get-NetTCPConnection -LocalPort 8000 -EA 0 | ? State -eq TimeWait) { sleep 1 }
```

3. Start the server:
```powershell
Start-Process -FilePath python -ArgumentList server.py -WorkingDirectory $PWD -WindowStyle Hidden
Start-Sleep 3  # give it time to bind
```

4. Verify:
```powershell
curl.exe -s http://localhost:8000/api/parking
```

### Why it hangs on restart

- **Multiple Python processes accumulate**: `Stop-Process` may target the wrong
  PID if a TIME_WAIT socket has OwningProcess=0. The old process survives, the
  new one starts but can't bind port 8000, and hangs silently.
- **Fix**: `http.server.HTTPServer.allow_reuse_address = True` in `server.py`
  allows immediate rebind. Also kill ALL python processes before restart.
- **Redirect deadlock**: `-RedirectStandardOutput` in `Start-Process` can cause
  a pipe buffer deadlock if the server blocks in `serve_forever()` without
  flushing stdout.

## Local Dev

```bash
python server.py
# → http://localhost:8000
# → http://192.168.50.251:8000   (on phone, same WiFi)
```

## Deployment

```bash
npm i -g vercel   # one-time
vercel --yes      # deploy
```

Then open the Vercel URL on phone → add to home screen.

**No laptop needed after install.** The PWA fetches data through Vercel's serverless
proxies (`api/parking.js`, `api/traffic.js`, `api/hours.js`) which use Node.js
`fetch` (not urllib) and work without issues.

## Files

| File | Purpose |
|---|---|
| `index.html` | Main app — Preact + HTM + Tailwind, glassmorphism |
| `manifest.json` | PWA install metadata |
| `sw.js` | Service worker — caches APIs offline |
| `icon.svg` | App icon |
| `server.py` | Python dev server + API proxy (curl-based), 3 endpoints |
| `api/parking.js` | Vercel proxy for parking API |
| `api/traffic.js` | Vercel proxy for traffic API |
| `api/hours.js` | Vercel proxy for hours (scrapes JSON-LD + holiday lookup) |
| `vercel.json` | Vercel config |
| `images/chaddy_map.png` | Parking map image |

## Troubleshooting History

### 2026-06-07 — Server hangs on restart
**Symptom**: After restart, port 8000 not listening, multiple Python processes
accumulate.  
**Cause**: Old process survived `Stop-Process` (TIME_WAIT port had PID 0 in
NetTCPConnection, so kill was skipped). New process couldn't bind.  
**Fixes applied**:
1. Added `HTTPServer.allow_reuse_address = True` in server.py
2. Kill ALL Python processes before restart
3. Avoid `-RedirectStandardOutput` with Start-Process
4. Wait for port TIME_WAIT to clear before starting

### 2026-06-07 — fetchApi CORS hang
**Symptom**: Browser showed infinite spinner on Finder/Planner tabs.  
**Cause**: `fetchApi()` tried `https://www.chadstone.com.au/api/parking` directly
first (CORS blocked), then fell back to local proxy. The direct request hung before
timing out.  
**Fix**: Removed direct Chadstone URL from fetchApi, only use relative `/api/*`
paths. Added 8s AbortController timeout.
