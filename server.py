"""
Jay Chaddy Parking Guide - local dev server.
Serves static files AND proxies API requests to Chadstone.
Usage: python server.py
"""
import http.server
import subprocess
import json
import datetime
import re

PORT = 8000

VIC_HOLIDAYS = {
    (6, 8): {"open": [10, 0], "close": [17, 0], "label": "King's Birthday"},
    (4, 18): {"open": [10, 0], "close": [17, 0], "label": "Good Friday"},
    (4, 20): {"open": [10, 0], "close": [17, 0], "label": "Easter Sunday"},
    (4, 21): {"open": [10, 0], "close": [17, 0], "label": "Easter Monday"},
    (1, 26): {"open": [10, 0], "close": [17, 0], "label": "Australia Day"},
    (1, 1): {"open": [10, 0], "close": [17, 0], "label": "New Year's Day"},
    (12, 25): {"open": [10, 0], "close": [17, 0], "label": "Christmas Day"},
    (12, 26): {"open": [10, 0], "close": [17, 0], "label": "Boxing Day"},
}


class Handler(http.server.SimpleHTTPRequestHandler):
    def _curl(self, url, timeout=10):
        result = subprocess.run(
            ["curl.exe", "-s", "-w", "\n%{http_code}", url],
            capture_output=True, text=False, timeout=timeout
        )
        decoded = result.stdout.decode("utf-8", errors="replace")
        lines = decoded.strip().split("\n")
        if len(lines) < 2:
            raise Exception("Empty response from curl")
        http_code = lines[-1].strip()
        body = "\n".join(lines[:-1])
        if http_code != "200":
            raise Exception(f"Upstream returned {http_code}")
        return body

    def _json_response(self, data, cache_seconds=30):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", f"public, max-age={cache_seconds}")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _error_response(self, msg):
        self.send_response(502)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps({"error": msg}).encode())

    def _proxy_api(self, path, base_url):
        try:
            url = base_url
            if "?" in path:
                url += "?" + path.split("?", 1)[1]
            data = self._curl(url)
            self._json_response(json.loads(data))
        except Exception as e:
            self._error_response(str(e))

    def _hours_data(self):
        try:
            html = self._curl("https://www.chadstone.com.au/")
            m = re.search(r'"openingHours"\s*:\s*"([^"]+)"', html)
            if not m:
                raise Exception("Could not find openingHours in JSON-LD")
            raw = m.group(1)

            today = datetime.date.today()
            monday = today - datetime.timedelta(days=today.weekday())
            week_holidays = []
            for i in range(14):
                d = monday + datetime.timedelta(days=i)
                h = VIC_HOLIDAYS.get((d.month, d.day))
                if h and all(x["weekday"] != (i + 1) % 7 or x["label"] != h["label"] for x in week_holidays):
                    def fmt_hm(hm):
                        h, m = hm
                        ampm = "am" if h < 12 else "pm"
                        h12 = h % 12
                        if h12 == 0:
                            h12 = 12
                        return f"{h12}:{m:02d}{ampm}"
                    week_holidays.append({
                        "weekday": (i + 1) % 7,
                        "label": h["label"],
                        "open": h["open"],
                        "close": h["close"],
                        "hours": f"{fmt_hm(h['open'])} – {fmt_hm(h['close'])}"
                    })
            holiday = VIC_HOLIDAYS.get((today.month, today.day))

            days_map = {
                "sunday": 0, "monday": 1, "tuesday": 2, "wednesday": 3,
                "thursday": 4, "friday": 5, "saturday": 6
            }

            slots = []
            for part in raw.split(","):
                part = part.strip()
                m2 = re.match(
                    r"(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)"
                    r"(?:\s+to\s+(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday))?"
                    r"\s+(\d{1,2}:\d{2}(?:am|pm))\s*[-–]\s*(\d{1,2}:\d{2}(?:am|pm))",
                    part, re.IGNORECASE
                )
                if m2:
                    start_day = m2.group(1).lower()
                    end_day = m2.group(2).lower() if m2.group(2) else start_day
                    open_str = m2.group(3)
                    close_str = m2.group(4)
                    slots.append((start_day, end_day, open_str, close_str))

            weekly = []
            for i, day_name in enumerate(["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]):
                open_time = close_time = None
                for sd, ed, op, cl in slots:
                    if days_map[sd] <= i <= days_map[ed]:
                        open_time = op
                        close_time = cl
                        break
                if open_time:
                    def parse_hm(s):
                        s = s.strip().lower()
                        is_pm = s.endswith("pm")
                        s = s.replace("am", "").replace("pm", "").strip()
                        h, m = map(int, s.split(":"))
                        if is_pm and h != 12:
                            h += 12
                        if not is_pm and h == 12:
                            h = 0
                        return [h, m]
                    weekly.append({
                        "day": day_name,
                        "open": parse_hm(open_time),
                        "close": parse_hm(close_time),
                        "hours": f"{open_time} – {close_time}"
                    })

            result = {
                "weekly": weekly,
                "holidays": week_holidays,
                "holiday": None,
                "cache_hint": "scraped"
            }

            if holiday:
                today_idx = today.weekday()
                day_name = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][today_idx]
                result["holiday"] = {
                    "date": today.isoformat(),
                    "label": holiday["label"],
                    "open": holiday["open"],
                    "close": holiday["close"],
                    "hours": f"{fmt_hm(holiday['open'])} – {fmt_hm(holiday['close'])}"
                }

            return result

        except Exception as e:
            return {"error": str(e), "using_fallback": True, "weekly": self._fallback_weekly()}

    def _fallback_weekly(self):
        return [
            {"day": "Sunday",    "open": [10, 0],  "close": [19, 0],  "hours": "10:00 am – 7:00 pm"},
            {"day": "Monday",    "open": [9, 0],   "close": [17, 30], "hours": "9:00 am – 5:30 pm"},
            {"day": "Tuesday",   "open": [9, 0],   "close": [17, 30], "hours": "9:00 am – 5:30 pm"},
            {"day": "Wednesday", "open": [9, 0],   "close": [17, 30], "hours": "9:00 am – 5:30 pm"},
            {"day": "Thursday",  "open": [9, 0],   "close": [21, 0],  "hours": "9:00 am – 9:00 pm"},
            {"day": "Friday",    "open": [9, 0],   "close": [21, 0],  "hours": "9:00 am – 9:00 pm"},
            {"day": "Saturday",  "open": [9, 0],   "close": [21, 0],  "hours": "9:00 am – 9:00 pm"},
        ]

    def do_GET(self):
        if self.path.startswith("/api/parking"):
            self._proxy_api(self.path, "https://www.chadstone.com.au/api/parking")
            return
        if self.path.startswith("/api/traffic"):
            self._proxy_api(self.path, "https://www.chadstone.com.au/api/traffic")
            return
        if self.path.startswith("/api/hours"):
            data = self._hours_data()
            if data.get("error"):
                self._error_response(data["error"])
            else:
                self._json_response(data, cache_seconds=3600)
            return
        return super().do_GET()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, format, *args):
        print(f"  {args[0]}")


if __name__ == "__main__":
    import os
    import socket

    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)

    http.server.HTTPServer.allow_reuse_address = True
    httpd = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"\n  Jay Chaddy Parking Guide")
    print(f"  Local:      http://localhost:{PORT}")
    print(f"  On Phone:   http://{local_ip}:{PORT}")
    print(f"  Proxies:    /api/parking /api/traffic /api/hours -> chadstone.com.au\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server stopped.")

