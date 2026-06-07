# Session: Live Hours API, Server Fixes, Parking Badge Themes

**Date:** 2026-06-07
**Branch:** `agent/chaddy-hours-live-server-fixes`
**Commit:** `b528700` feat(chaddy): live hours API, parking badge themes, CORS fix, server stability

## Goal
Make opening hours live (not hardcoded), add car park letter themes, fix CORS hang, stabilize dev server restarts.

## Files Changed

| File | Change |
|---|---|
| `server.py` | Added `/api/hours` endpoint (scrapes JSON-LD from Chadstone homepage), `HTTPServer.allow_reuse_address = True`, UTF-8 encoding fix for curl output, refactored into helper methods |
| `index.html` | Added `fetchHours()` + `hoursData` state, Hours component accepts `data` prop with live API fallback, car park theme colors (THEME map), simplified `fetchApi` with AbortController + timeout, error states for Finder/Planner |
| `api/hours.js` | New Vercel serverless proxy — scrapes Chadstone homepage JSON-LD, parses into daily hours, checks VIC public holiday lookup |
| `plan.md` | Updated endpoints table, added startup recipe, restart procedure, troubleshooting history |
| `sw.js` | (no change) |
| `manifest.json` | (no change) |
| `vercel.json` | (no change) |

## Commands Executed

- `python server.py` — dev server
- `curl.exe` tests for all API endpoints (parking, traffic, hours, static files)
- Git: create branch, add, commit
- `Start-Process` for background server

## Important Decisions

### 1. Hours API approach
**Decision:** Scrape JSON-LD `openingHours` from Chadstone homepage instead of using Storyblok CMS API or hardcoded data.
**Why:** The homepage has clean schema.org `openingHours` in JSON-LD. The Storyblok CMS data is rendered client-side by React and not directly accessible. The JSON-LD is always up-to-date with Chadstone's actual hours.

### 2. Holiday detection
**Decision:** Hardcoded VIC public holiday lookup table in both `server.py` and `api/hours.js`.
**Why:** Chadstone's JSON-LD only shows standard weekly hours, not holiday variations. A lookup table for major VIC public holidays (King's Birthday, Easter, Christmas, etc.) is the simplest reliable approach.

### 3. CORS hang fix
**Decision:** Removed direct Chadstone URL from `fetchApi()` fallback chain, added 8s AbortController timeout.
**Why:** The browser CORS preflight to `https://www.chadstone.com.au/api/parking` from localhost hangs before timing out (minutes). The relative `/api/*` path should always work via the local proxy or Vercel serverless.

### 4. Server restart hangs
**Decision:** Added `HTTPServer.allow_reuse_address = True`, documented correct startup method (`-WindowStyle Hidden`, no `-RedirectStandardOutput`).
**Why:** Three issues compounded: race condition in kill logic (TIME_WAIT socket had PID 0), missing SO_REUSEADDR, stdout pipe deadlock with `-RedirectStandardOutput`.

## Blockers
- None. All 6 endpoints verified returning 200 with correct data.
