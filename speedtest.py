#!/usr/bin/env python3
"""
Internet Speed Test — multi-server, parallel-stream edition
Tests download and upload speeds, shows real-time progress bars,
saves results to a timestamped file.
"""

import sys
import os
import time
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

try:
    import requests
    from tqdm import tqdm
except ImportError:
    print("\nMissing required packages. Install them with:")
    print("  pip install requests tqdm")
    sys.exit(1)

# ── constants ──────────────────────────────────────────────────────────────────

BAR_FMT = "{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]"

CF_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Origin":  "https://speed.cloudflare.com",
    "Referer": "https://speed.cloudflare.com/",
}

UPLOAD_URL = "https://speed.cloudflare.com/__up"   # only reliable public upload endpoint

# Download server definitions.
# dynamic=True  → URL template with {size} byte param (Cloudflare).
# dynamic=False → fixed files; sm_* for ≤250 MB tests, lg_* for 1 GB tests.
DOWNLOAD_SERVERS = [
    {
        "id":      1,
        "name":    "Cloudflare",
        "short":   "Cloudflare",
        "dynamic": True,
        "url_tmpl": "https://speed.cloudflare.com/__down?bytes={size}",
        "headers": CF_HEADERS,
    },
    {
        "id":       2,
        "name":     "Linode (Dallas, US)",
        "short":    "Linode-US",
        "dynamic":  False,
        "sm_url":   "https://speedtest.dallas.linode.com/100MB-dallas.bin",
        "sm_bytes": 100 * 1024 * 1024,
        "lg_url":   "https://speedtest.dallas.linode.com/1GB-dallas.bin",
        "lg_bytes": 1024 * 1024 * 1024,
        "headers":  {},
    },
    {
        "id":       3,
        "name":     "Tele2 (Stockholm, EU)",
        "short":    "Tele2-EU",
        "dynamic":  False,
        "sm_url":   "http://speedtest.tele2.net/100MB.zip",
        "sm_bytes": 100 * 1024 * 1024,
        "lg_url":   "http://speedtest.tele2.net/1GB.zip",
        "lg_bytes": 1024 * 1024 * 1024,
        "headers":  {},
    },
    {
        "id":       4,
        "name":     "OVH (Beauharnois, CA)",
        "short":    "OVH",
        "dynamic":  False,
        "sm_url":   "https://proof.ovh.net/files/100Mb.dat",
        "sm_bytes": 100 * 1024 * 1024,
        "lg_url":   "https://proof.ovh.net/files/1Gb.dat",
        "lg_bytes": 1024 * 1024 * 1024,
        "headers":  {},
    },
]

SIZE_OPTIONS = [
    ("100 MB",   100 * 1024 * 1024),
    ("250 MB",   250 * 1024 * 1024),
    ("1 GB",    1024 * 1024 * 1024),
]

# ── helpers ────────────────────────────────────────────────────────────────────

def mbps(bytes_per_sec: float) -> float:
    return (bytes_per_sec * 8) / (1024 * 1024)


def fmt_size(n: int) -> str:
    if n >= 1024 ** 3:
        return f"{n / 1024 ** 3:.2f} GB"
    if n >= 1024 ** 2:
        return f"{n / 1024 ** 2:.1f} MB"
    return f"{n / 1024:.1f} KB"


def ask(prompt: str) -> bool:
    while True:
        r = input(f"{prompt} [y/n]: ").strip().lower()
        if r in ("y", "yes"):
            return True
        if r in ("n", "no"):
            return False
        print("  Please enter y or n.")


def ask_int(prompt: str, default: int, lo: int, hi: int) -> int:
    while True:
        raw = input(f"{prompt} [{lo}-{hi}, default {default}]: ").strip()
        if not raw:
            return default
        try:
            v = int(raw)
            if lo <= v <= hi:
                return v
            print(f"  Enter a number between {lo} and {hi}.")
        except ValueError:
            print("  Invalid number.")


# ── selection prompts ──────────────────────────────────────────────────────────

def choose_sizes() -> list[tuple[str, int]]:
    print("\n  Test sizes:")
    for i, (name, _) in enumerate(SIZE_OPTIONS, 1):
        print(f"    {i}. {name}")
    print(f"    {len(SIZE_OPTIONS) + 1}. All sizes")

    while True:
        raw    = input("\n  Select size(s) — enter number(s) separated by spaces: ").strip()
        tokens = raw.split()
        if not tokens:
            print("  No selection made, try again.")
            continue
        if str(len(SIZE_OPTIONS) + 1) in tokens or raw.lower() == "all":
            return list(SIZE_OPTIONS)
        selected, valid = [], True
        for t in tokens:
            try:
                idx = int(t) - 1
                if 0 <= idx < len(SIZE_OPTIONS):
                    entry = SIZE_OPTIONS[idx]
                    if entry not in selected:
                        selected.append(entry)
                else:
                    print(f"  '{t}' is out of range.")
                    valid = False
                    break
            except ValueError:
                print(f"  '{t}' is not a valid number.")
                valid = False
                break
        if valid and selected:
            return selected
        print("  Please try again.")


def choose_servers() -> list[dict]:
    print("\n  Download servers:")
    for s in DOWNLOAD_SERVERS:
        tag = "dynamic size" if s["dynamic"] else "100 MB / 1 GB fixed files"
        print(f"    {s['id']}. {s['name']:<28} ({tag})")
    print(f"    {len(DOWNLOAD_SERVERS) + 1}. All servers")

    while True:
        raw    = input("\n  Select server(s) — enter number(s) separated by spaces: ").strip()
        tokens = raw.split()
        if not tokens:
            print("  No selection made, try again.")
            continue
        if str(len(DOWNLOAD_SERVERS) + 1) in tokens or raw.lower() == "all":
            return list(DOWNLOAD_SERVERS)
        selected, valid = [], True
        for t in tokens:
            try:
                idx = int(t) - 1
                if 0 <= idx < len(DOWNLOAD_SERVERS):
                    entry = DOWNLOAD_SERVERS[idx]
                    if entry not in selected:
                        selected.append(entry)
                else:
                    print(f"  '{t}' is out of range.")
                    valid = False
                    break
            except ValueError:
                print(f"  '{t}' is not a valid number.")
                valid = False
                break
        if valid and selected:
            return selected
        print("  Please try again.")


# ── upload helper ──────────────────────────────────────────────────────────────

class _ProgressReader:
    """Thread-safe file-like object that streams pseudo-random data with tqdm progress.

    Reuses a single 1 MB class-level buffer (read-only) so arbitrarily large
    uploads never exceed ~1 MB of extra RAM per instance.  Implements seek/tell
    so requests sets Content-Length and avoids chunked encoding (Cloudflare rejects it).
    """
    _BUF: bytes = os.urandom(1024 * 1024)   # 1 MB, shared across all instances

    def __init__(self, size_bytes: int, bar, lock: threading.Lock):
        self._size = size_bytes
        self._pos  = 0
        self._bar  = bar
        self._lock = lock

    def __len__(self) -> int:
        return self._size

    def read(self, n: int = -1) -> bytes:
        if self._pos >= self._size:
            return b""
        if n < 0:
            n = self._size - self._pos
        to_read = min(n, self._size - self._pos)

        result  = bytearray(to_read)
        filled  = 0
        buf     = self._BUF
        buf_len = len(buf)
        while filled < to_read:
            off  = self._pos % buf_len
            take = min(to_read - filled, buf_len - off)
            result[filled : filled + take] = buf[off : off + take]
            filled    += take
            self._pos += take

        data = bytes(result)
        with self._lock:
            self._bar.update(len(data))
        return data

    def seek(self, pos: int, whence: int = 0) -> int:
        if whence == 0:
            self._pos = pos
        elif whence == 1:
            self._pos += pos
        elif whence == 2:
            self._pos = self._size + pos
        self._pos = max(0, min(self._pos, self._size))
        return self._pos

    def tell(self) -> int:
        return self._pos


# ── download ───────────────────────────────────────────────────────────────────

def _dl_worker(url: str, headers: dict, bar, lock: threading.Lock) -> int:
    received = 0
    with requests.get(url, stream=True, timeout=120, headers=headers) as r:
        r.raise_for_status()
        for chunk in r.iter_content(chunk_size=65_536):
            if chunk:
                received += len(chunk)
                with lock:
                    bar.update(len(chunk))
    return received


def run_download(size_bytes: int, size_label: str, server: dict, streams: int) -> dict:
    hdrs = server["headers"]

    if server["dynamic"]:
        per    = size_bytes // streams
        rem    = size_bytes - per * streams
        sizes  = [per] * streams
        if rem:
            sizes[-1] += rem
        urls   = [server["url_tmpl"].format(size=s) for s in sizes]
        total  = size_bytes
        note   = ""
    else:
        # Pick the appropriate fixed file
        if size_bytes <= 250 * 1024 * 1024:
            url, file_bytes = server["sm_url"], server["sm_bytes"]
        else:
            url, file_bytes = server["lg_url"], server["lg_bytes"]
        urls  = [url] * streams
        total = file_bytes * streams
        note  = f" [{fmt_size(file_bytes)} × {streams}]"

    lock = threading.Lock()
    desc = f"  DL {server['short']:<12}"
    with tqdm(
        total=total, unit="B", unit_scale=True, unit_divisor=1024,
        desc=desc, bar_format=BAR_FMT, ncols=82,
    ) as bar:
        t0 = time.perf_counter()
        with ThreadPoolExecutor(max_workers=streams) as ex:
            results = list(ex.map(lambda u: _dl_worker(u, hdrs, bar, lock), urls))

    elapsed = time.perf_counter() - t0
    total_rx = sum(results)
    return {
        "server":  server["name"],
        "label":   size_label + note,
        "bytes":   total_rx,
        "elapsed": elapsed,
        "mbps":    mbps(total_rx / elapsed),
    }


# ── upload ─────────────────────────────────────────────────────────────────────

def _ul_worker(size_bytes: int, bar, lock: threading.Lock) -> int:
    reader = _ProgressReader(size_bytes, bar, lock)
    resp   = requests.post(
        UPLOAD_URL, data=reader,
        headers={**CF_HEADERS, "Content-Type": "application/octet-stream"},
        timeout=600,
    )
    resp.raise_for_status()
    return size_bytes


def run_upload(size_bytes: int, size_label: str, streams: int) -> dict:
    per   = size_bytes // streams
    rem   = size_bytes - per * streams
    sizes = [per] * streams
    if rem:
        sizes[-1] += rem

    lock = threading.Lock()
    desc = f"  UL {'Cloudflare':<12}"
    with tqdm(
        total=size_bytes, unit="B", unit_scale=True, unit_divisor=1024,
        desc=desc, bar_format=BAR_FMT, ncols=82,
    ) as bar:
        t0 = time.perf_counter()
        with ThreadPoolExecutor(max_workers=streams) as ex:
            results = list(ex.map(lambda s: _ul_worker(s, bar, lock), sizes))

    elapsed  = time.perf_counter() - t0
    total_tx = sum(results)
    return {
        "server":  "Cloudflare",
        "label":   size_label,
        "bytes":   total_tx,
        "elapsed": elapsed,
        "mbps":    mbps(total_tx / elapsed),
    }


# ── results ────────────────────────────────────────────────────────────────────

def build_report(dl_results: list, ul_results: list, ts: str, streams: int) -> str:
    W = 68
    lines = [
        "=" * W,
        "  INTERNET SPEED TEST RESULTS".center(W),
        f"  {ts}  ·  {streams} parallel stream{'s' if streams > 1 else ''}".center(W),
        "=" * W,
    ]

    def section(title: str, results: list):
        lines.append(f"\n  {title}")
        lines.append("  " + "-" * (W - 2))
        for r in results:
            lines.append(
                f"    {r['server']:<26} {r['label']:<10}"
                f"  {r['mbps']:>8.2f} Mbps"
                f"   ({fmt_size(r['bytes'])} in {r['elapsed']:.1f}s)"
            )
        if len(results) > 1:
            avg = sum(r["mbps"] for r in results) / len(results)
            lines.append(f"    {'Average':<26} {'':10}  {avg:>8.2f} Mbps")

    if dl_results:
        section("DOWNLOAD", dl_results)
    if ul_results:
        section("UPLOAD", ul_results)

    lines.append("\n" + "=" * W)
    return "\n".join(lines)


def save_report(text: str, ts: str) -> str:
    safe_ts = ts.replace(" ", "_").replace(":", "-")
    fname   = f"speedtest_{safe_ts}.txt"
    with open(fname, "w") as fh:
        fh.write(text + "\n")
    return fname


# ── main ───────────────────────────────────────────────────────────────────────

def main():
    print("\n" + "=" * 68)
    print("     INTERNET SPEED TEST  (multi-server · parallel streams)".center(68))
    print("=" * 68)

    do_dl = ask("\nTest download speed?")
    do_ul = ask("Test upload speed?")

    if not do_dl and not do_ul:
        print("No tests selected. Exiting.")
        sys.exit(0)

    streams = ask_int(
        "\nParallel streams per test (more = closer to true line speed)", 4, 1, 16
    )

    use_sizes = ask("\nTest with multiple file sizes (100 MB / 250 MB / 1 GB)?")
    sizes     = choose_sizes() if use_sizes else [SIZE_OPTIONS[0]]

    dl_servers: list[dict] = []
    if do_dl:
        dl_servers = choose_servers()

    print("\n" + "=" * 68)
    print(f"  Starting tests  ({streams} parallel stream{'s' if streams > 1 else ''})…")
    print("=" * 68)

    dl_results: list[dict] = []
    ul_results: list[dict] = []

    for size_label, size_bytes in sizes:
        if do_dl:
            for server in dl_servers:
                print(f"\nDownload — {size_label}  [{server['name']}]")
                try:
                    dl_results.append(run_download(size_bytes, size_label, server, streams))
                except Exception as exc:
                    print(f"  [ERROR] {exc}")

        if do_ul:
            print(f"\nUpload — {size_label}  [Cloudflare, {streams} streams]")
            try:
                ul_results.append(run_upload(size_bytes, size_label, streams))
            except Exception as exc:
                print(f"  [ERROR] {exc}")

    ts     = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = build_report(dl_results, ul_results, ts, streams)

    print("\n")
    print(report)

    fname = save_report(report, ts)
    print(f"\n  Results saved to: {fname}\n")


if __name__ == "__main__":
    main()
