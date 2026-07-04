# 🅿️ Chaddy Parking Guide

> Real-time parking occupancy, 7-day traffic forecasts, opening hours & interactive map for **Chadstone Shopping Centre** — Melbourne's premier retail destination.

[![Vercel](https://img.shields.io/badge/deployed%20on-Vercel-000?logo=vercel)](https://chaddy-parking.vercel.app)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**👉 https://chaddy-parking.vercel.app**

---

## About Chadstone

Since opening its doors in **1960**, Chadstone has grown into Australia's leading shopping destination, integrating the world's best retail, hospitality and lifestyle offering under one roof. With **over 500 local and international brands**, **90+ fresh food and dining options**, entertainment for all, valet service and **over 10,000 free parking spaces**, Chadstone continues to create inspiring environments for generations of visitors.

### The Parking Problem

If you've ever driven to Chaddy on a weekend, a public holiday, or during the Boxing Day sales, you know the drill: you cruise through Car Park A, then B, then C… circling for 20 minutes while the kids get restless and your parked-where? text chain begins.

Chadstone is **infamous** for its challenging parking. The layout is sprawling, the popular car parks fill up fast, and by the time you spot a "FULL" sign, you're already committed to a maze of one-way ramps. **Planning ahead isn't just convenient — it's essential.**

This app helps you arrive with a plan: which car park has space right now, what time the crowds peak today, and exactly where you're headed on the map.

---

## Features

### 🔍 Parking Finder
Live occupancy for every public car park (A–F), plus a total overview:

| Car Park | Location |
|---|---|
| **A** — David Jones | Northern end, near David Jones & luxury brands |
| **B** — Social Quarter / HOYTS | Near the dining precinct & cinema |
| **C** — Market Pavilion / Coles | Central, near Coles & fresh food |
| **D** — Private Parking | Reserved parking (not publicly available) |
| **E** — Woolworths / Dining | Southern end, near Woolworths & restaurants |
| **F** — Myer | Near Myer & the fashion precinct |

Each car park shows:
- **Free spaces available** — live count
- **Occupancy percentage** — colour-coded bar (green / yellow / red)
- **Status label** — *Plenty of space*, *Filling up*, or *Near capacity*

Auto-refreshes every **60 seconds** so you're never looking at stale data.

### 📊 Visit Planner
A 7-day hourly traffic forecast with an interactive bar chart:
- **Peak hour** — the busiest time of day (avoid this!)
- **Best time** — the quietest window (aim for this!)
- **Now marker** — a pulsing indicator on today's chart showing the current hour
- **Day navigation** — flip through the week to plan future visits
- Auto-refreshes every **5 minutes** in the background

Green bars = quiet, yellow = busy, red = packed.

### 🕐 Opening Hours
Live centre trading hours scraped directly from Chadstone's website, including:
- Today's status (*Open now* with countdown to close, or *Closed* with countdown to open)
- Full weekly schedule
- Public holiday hours (VIC holidays detected automatically)
- Market Pavilion & Social Quarter precinct hours

### 🗺️ Parking Map
An interactive map of the Chadstone parking layout:
- **Pinch to zoom** (mobile) or **scroll to zoom** (desktop)
- **Drag to pan**
- **Double-tap to reset** zoom to default
- Works offline once loaded (cached by service worker)

---

## How It Works

### Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | [Preact](https://preactjs.com/) + [HTM](https://github.com/developit/htm) + [Tailwind CSS](https://tailwindcss.com/) (CDN) |
| **API Proxy** | [Vercel Serverless Functions](https://vercel.com/docs/functions) (Node.js) |
| **Dev Server** | Python (`server.py`) with `curl` proxy |
| **Offline** | Service Worker (`sw.js`) caches API responses for offline fallback |
| **Data Source** | [Chadstone public API](https://www.chadstone.com.au/) |

### Data Flow

```
Browser → Service Worker → Vercel Serverless → Chadstone API
                ↕                  ↕
          Cache Storage      Server-side fetch
          (offline fallback)  (avoids CORS)
```

1. **Parking data** — hits `/api/parking` → Vercel proxies to `chadstone.com.au/api/parking` → returns live occupancy for car parks A–F
2. **Traffic data** — hits `/api/traffic?startDate=...` → Vercel proxies to `chadstone.com.au/api/traffic` → returns 7-day hourly forecasts
3. **Hours data** — hits `/api/hours` → Vercel scrapes opening hours from Chadstone's homepage JSON-LD + VIC public holiday lookup

### Offline & Caching

The service worker uses a **network-first** strategy:
- On success: response is cached and returned fresh
- On failure: cached response is served as fallback
- The app also falls back to `localStorage` if the API is unreachable

Both the **Parking Finder** (60s) and **Visit Planner** (5min) auto-refresh in the background while the tab is visible. The countdown pauses when you switch tabs.

---

## Getting Started (Development)

### Prerequisites

- [Python 3](https://www.python.org/) (for local dev server)
- [curl](https://curl.se/) (for API proxy — the Chadstone API blocks Python's `urllib`)
- [Node.js](https://nodejs.org/) (for Vercel deployment)

### Local Dev

```bash
python server.py
```

Then open **http://localhost:8000** in your browser.

The dev server serves the static files and proxies `/api/parking`, `/api/traffic`, and `/api/hours` to `chadstone.com.au`.

> **Note**: On Windows, start the server with `Start-Process` to avoid stdout deadlock:
> ```powershell
> Start-Process -FilePath python -ArgumentList server.py -WindowStyle Hidden
> ```

### Deploy to Vercel

```bash
npm i -g vercel   # one-time
vercel --yes      # deploy preview
vercel --prod     # deploy to production
```

The project is already configured for Vercel — no additional setup needed.

---

## Project Structure

```
├── api/
│   ├── hours.js       # Vercel serverless — scrapes opening hours
│   ├── parking.js     # Vercel serverless — proxies parking data
│   └── traffic.js     # Vercel serverless — proxies traffic forecasts
├── images/
│   └── chaddy_map.png # Interactive parking map
├── docs/
│   └── agent-sessions/  # Development session notes
├── index.html         # Single-page app (Preact + HTM)
├── manifest.json      # PWA manifest
├── sw.js              # Service worker (offline caching)
├── server.py          # Python dev server
├── vercel.json        # Vercel deployment config
└── plan.md            # Architecture & troubleshooting notes
```

---

## Acknowledgements

- **Chadstone Shopping Centre** for providing the public API endpoints and JSON-LD structured data
- All Sydney-siders and Melburnians who've circled a car park three times too many — this one's for you

---

*pairing.planning.chadstone*
