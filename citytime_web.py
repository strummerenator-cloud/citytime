#!/usr/bin/env python3
"""Web UI server for citytime.py"""
import os
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, available_timezones

from flask import Flask, jsonify, request, render_template, abort

# Add the directory containing citytime.py to the path
sys.path.insert(0, str(Path(__file__).parent))
from citytime import (
    load_aliases, save_alias, is_valid_timezone,
    find_timezone_matches, ALIAS_FILE
)

app = Flask(__name__)

# Cache the sorted timezone list at startup
_ALL_TIMEZONES = sorted(available_timezones())


def _resolve_city(city: str):
    """Resolve a city name to (timezone_str, display_name) or None."""
    city_norm = city.lower().strip()
    aliases = load_aliases()

    # Direct alias/city lookup
    tz = aliases.get(city_norm)
    if tz and is_valid_timezone(tz):
        return tz, city

    # Maybe the input is already a valid IANA timezone
    if is_valid_timezone(city_norm) or is_valid_timezone(city):
        return city if is_valid_timezone(city) else city_norm, city

    # Fuzzy match (top result only, no interactive prompts)
    matches = find_timezone_matches(city_norm)
    if matches and matches[0][1] >= 0.8:
        return matches[0][0], city

    return None, city


@app.route("/debug-test")
def debug_test():
    raise Exception("test error")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/time/<path:city>")
def api_get_time(city: str):
    tz_str, display = _resolve_city(city)
    if not tz_str:
        return jsonify({"error": f"City '{city}' not found"}), 404

    try:
        tz_info = ZoneInfo(tz_str)
        now = datetime.now(tz_info)
        offset = now.strftime("%z")
        offset_fmt = f"UTC{offset[:3]}:{offset[3:]}" if offset else "UTC"
        return jsonify({
            "city": city,
            "timezone": tz_str,
            "iso": now.isoformat(),
            "time": now.strftime("%H:%M:%S"),
            "date": now.strftime("%Y-%m-%d"),
            "offset": offset_fmt,
            "abbr": now.strftime("%Z"),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/aliases", methods=["GET"])
def api_list_aliases():
    aliases = load_aliases()
    return jsonify(aliases)


@app.route("/api/aliases", methods=["POST"])
def api_add_alias():
    data = request.get_json(force=True, silent=True) or {}
    city = (data.get("city") or "").strip().lower()
    timezone = (data.get("timezone") or "").strip()

    if not city:
        return jsonify({"error": "city is required"}), 400
    if not timezone:
        return jsonify({"error": "timezone is required"}), 400
    if not is_valid_timezone(timezone):
        return jsonify({"error": f"Invalid timezone: {timezone}"}), 400

    save_alias(city, timezone)
    return jsonify({"ok": True, "city": city, "timezone": timezone})


@app.route("/api/aliases/<path:city>", methods=["DELETE"])
def api_delete_alias(city: str):
    city = city.strip().lower()
    if not ALIAS_FILE.exists():
        return jsonify({"error": "Alias not found"}), 404

    with open(ALIAS_FILE, "r") as f:
        lines = f.readlines()

    new_lines = [l for l in lines if not l.startswith(f"{city}=")]
    if len(new_lines) == len(lines):
        return jsonify({"error": f"'{city}' not found in user aliases"}), 404

    temp = ALIAS_FILE.with_suffix(".tmp")
    with open(temp, "w") as f:
        f.writelines(new_lines)
    temp.replace(ALIAS_FILE)

    return jsonify({"ok": True, "removed": city})


@app.route("/api/timezones")
def api_timezones():
    return jsonify(_ALL_TIMEZONES)


_headlines_cache: dict = {"data": None, "expires": None}

@app.route("/api/headlines")
def api_headlines():
    now = datetime.now(timezone.utc)
    if _headlines_cache["data"] and _headlines_cache["expires"] and now < _headlines_cache["expires"]:
        return jsonify(_headlines_cache["data"])
    try:
        url = "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            xml_data = resp.read()
        root = ET.fromstring(xml_data)
        channel = root.find("channel")
        items = channel.findall("item")[:6]
        headlines = []
        for item in items:
            title_el = item.find("title")
            link_el = item.find("link")
            if title_el is not None and link_el is not None:
                title = title_el.text or ""
                link = link_el.text or ""
                if " - " in title:
                    title = title.rsplit(" - ", 1)[0]
                headlines.append({"title": title, "url": link})
        _headlines_cache["data"] = headlines
        _headlines_cache["expires"] = now + timedelta(minutes=10)
        return jsonify(headlines)
    except Exception:
        if _headlines_cache["data"]:
            return jsonify(_headlines_cache["data"])
        return jsonify([])


@app.route("/api/search/<path:query>")
def api_search(query: str):
    query_norm = query.lower().strip()
    aliases = load_aliases()

    results = []
    seen_tz = set()

    # Exact + partial alias matches first
    for city, tz in sorted(aliases.items()):
        if query_norm in city:
            if tz not in seen_tz:
                seen_tz.add(tz)
            results.append({"city": city, "timezone": tz, "score": 1.0 if city == query_norm else 0.9})
        if len(results) >= 20:
            break

    # Fuzzy timezone matches if we need more
    if len(results) < 10:
        matches = find_timezone_matches(query_norm)
        for tz, score in matches[:10]:
            city_label = os.path.basename(tz).replace("_", " ")
            results.append({"city": city_label, "timezone": tz, "score": score})

    # Deduplicate by (city, tz) and limit
    seen = set()
    deduped = []
    for r in results:
        key = (r["city"], r["timezone"])
        if key not in seen:
            seen.add(key)
            deduped.append(r)

    deduped.sort(key=lambda x: x["score"], reverse=True)
    return jsonify(deduped[:15])


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting CityTime web UI at http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)
