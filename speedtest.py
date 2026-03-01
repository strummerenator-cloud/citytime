#!/usr/bin/env python3
"""
Internet Speed Test
Tests download and upload speeds via Cloudflare's speed test endpoints.
Shows real-time progress bars and saves results to a timestamped file.
"""

import sys
import os
import time
from datetime import datetime

try:
    import requests
    from tqdm import tqdm
except ImportError:
    print("\nMissing required packages. Install them with:")
    print("  pip install requests tqdm")
    sys.exit(1)

DOWNLOAD_URL = "https://speed.cloudflare.com/__down"
UPLOAD_URL   = "https://speed.cloudflare.com/__up"

# Browser-like headers required by Cloudflare's speed test endpoints
CF_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Origin":  "https://speed.cloudflare.com",
    "Referer": "https://speed.cloudflare.com/",
}

SIZE_OPTIONS = [
    ("100 MB",   100 * 1024 * 1024),
    ("250 MB",   250 * 1024 * 1024),
    ("1 GB",    1024 * 1024 * 1024),
]

BAR_FMT = "{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]"


# ── helpers ───────────────────────────────────────────────────────────────────

def mbps(bytes_per_sec: float) -> float:
    return (bytes_per_sec * 8) / (1024 * 1024)


def fmt_size(n: int) -> str:
    if n >= 1024 ** 3:
        return f"{n / 1024 ** 3:.1f} GB"
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


# ── size selection ─────────────────────────────────────────────────────────────

def choose_sizes() -> list[tuple[str, int]]:
    print("\n  Available test sizes:")
    for i, (name, _) in enumerate(SIZE_OPTIONS, 1):
        print(f"    {i}. {name}")
    print(f"    {len(SIZE_OPTIONS)+1}. All sizes")

    while True:
        raw = input("\n  Select size(s) — enter number(s) separated by spaces: ").strip()
        tokens = raw.split()
        if not tokens:
            print("  No selection made, try again.")
            continue

        # "all" choice
        if str(len(SIZE_OPTIONS) + 1) in tokens or raw.lower() == "all":
            return list(SIZE_OPTIONS)

        selected = []
        valid = True
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


# ── speed tests ────────────────────────────────────────────────────────────────

def run_download(size_bytes: int, label: str) -> dict:
    url = f"{DOWNLOAD_URL}?bytes={size_bytes}"
    received = 0
    chunk = 65_536  # 64 KB

    with requests.get(url, stream=True, timeout=120, headers=CF_HEADERS) as resp:
        resp.raise_for_status()
        t0 = time.perf_counter()
        with tqdm(
            total=size_bytes, unit="B", unit_scale=True, unit_divisor=1024,
            desc=f"  DL {label}", bar_format=BAR_FMT, ncols=80,
        ) as bar:
            for data in resp.iter_content(chunk_size=chunk):
                if data:
                    received += len(data)
                    bar.update(len(data))

    elapsed = time.perf_counter() - t0
    return {"label": label, "bytes": received, "elapsed": elapsed,
            "mbps": mbps(received / elapsed)}


class _ProgressReader:
    """File-like object that streams pseudo-random data and tracks upload progress.

    Reuses a single 1 MB buffer so arbitrarily large uploads never exceed ~1 MB
    of extra RAM.  Implements seek/tell so requests can determine Content-Length
    and avoids chunked transfer encoding (which Cloudflare rejects).
    """
    _BUF_SIZE = 1024 * 1024  # 1 MB pre-generated pattern

    def __init__(self, size_bytes: int, pbar):
        self._size  = size_bytes
        self._pos   = 0
        self._pbar  = pbar
        self._buf   = os.urandom(self._BUF_SIZE)

    def __len__(self) -> int:
        return self._size

    def read(self, n: int = -1) -> bytes:
        if self._pos >= self._size:
            return b""
        if n < 0:
            n = self._size - self._pos
        to_read = min(n, self._size - self._pos)

        result = bytearray(to_read)
        filled = 0
        while filled < to_read:
            buf_off  = self._pos % self._BUF_SIZE
            take     = min(to_read - filled, self._BUF_SIZE - buf_off)
            result[filled : filled + take] = self._buf[buf_off : buf_off + take]
            filled      += take
            self._pos   += take

        data = bytes(result)
        self._pbar.update(len(data))
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


def run_upload(size_bytes: int, label: str) -> dict:
    with tqdm(
        total=size_bytes, unit="B", unit_scale=True, unit_divisor=1024,
        desc=f"  UL {label}", bar_format=BAR_FMT, ncols=80,
    ) as bar:
        reader = _ProgressReader(size_bytes, bar)
        t0 = time.perf_counter()
        resp = requests.post(
            UPLOAD_URL, data=reader,
            headers={
                **CF_HEADERS,
                "Content-Type": "application/octet-stream",
            },
            timeout=600,
        )
        resp.raise_for_status()

    elapsed = time.perf_counter() - t0
    return {"label": label, "bytes": size_bytes, "elapsed": elapsed,
            "mbps": mbps(size_bytes / elapsed)}


# ── results ────────────────────────────────────────────────────────────────────

def build_report(dl_results: list, ul_results: list, ts: str) -> str:
    W = 62
    lines = [
        "=" * W,
        "  INTERNET SPEED TEST RESULTS".center(W),
        f"  {ts}".center(W),
        "=" * W,
    ]

    def section(title, results):
        lines.append(f"\n  {title}")
        lines.append("  " + "-" * (W - 2))
        for r in results:
            lines.append(
                f"    {r['label']:<8}  {r['mbps']:>8.2f} Mbps"
                f"   ({fmt_size(r['bytes'])} in {r['elapsed']:.1f}s)"
            )
        if len(results) > 1:
            avg = sum(r["mbps"] for r in results) / len(results)
            lines.append(f"    {'Average':<8}  {avg:>8.2f} Mbps")

    if dl_results:
        section("DOWNLOAD", dl_results)
    if ul_results:
        section("UPLOAD", ul_results)

    lines.append("\n" + "=" * W)
    return "\n".join(lines)


def save_report(text: str, ts: str) -> str:
    safe_ts = ts.replace(" ", "_").replace(":", "-")
    fname = f"speedtest_{safe_ts}.txt"
    with open(fname, "w") as fh:
        fh.write(text + "\n")
    return fname


# ── main ───────────────────────────────────────────────────────────────────────

def main():
    print("\n" + "=" * 62)
    print("           INTERNET SPEED TEST".center(62))
    print("=" * 62)
    print("\nUsing Cloudflare speed test endpoints.")

    do_dl = ask("\nTest download speed?")
    do_ul = ask("Test upload speed?")

    if not do_dl and not do_ul:
        print("No tests selected. Exiting.")
        sys.exit(0)

    use_sizes = ask("\nTest with multiple file sizes (100 MB / 250 MB / 1 GB)?")
    if use_sizes:
        sizes = choose_sizes()
    else:
        sizes = [("100 MB", SIZE_OPTIONS[0][1])]

    print("\n" + "=" * 62)
    print("  Starting tests…")
    print("=" * 62)

    dl_results: list[dict] = []
    ul_results: list[dict] = []

    for label, size_bytes in sizes:
        if do_dl:
            print(f"\nDownload — {label}")
            try:
                dl_results.append(run_download(size_bytes, label))
            except Exception as exc:
                print(f"  [ERROR] Download {label} failed: {exc}")

        if do_ul:
            print(f"\nUpload — {label}")
            try:
                ul_results.append(run_upload(size_bytes, label))
            except Exception as exc:
                print(f"  [ERROR] Upload {label} failed: {exc}")

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = build_report(dl_results, ul_results, ts)

    print("\n")
    print(report)

    fname = save_report(report, ts)
    print(f"\n  Results saved to: {fname}\n")


if __name__ == "__main__":
    main()
