"""Step 1: download the public source files into data/raw/.

Files already present are skipped, so manually downloaded copies are respected.
"""
import sys

import requests

from config import RAW, SOURCES


def main() -> int:
    RAW.mkdir(parents=True, exist_ok=True)
    failed = []
    for key, src in SOURCES.items():
        dest = RAW / src["local"]
        if dest.exists() and dest.stat().st_size > 0:
            print(f"[skip] {dest.name} already present")
            continue
        print(f"[get ] {key}: {src['url']}")
        try:
            with requests.get(src["url"], stream=True, timeout=300,
                              headers={"User-Agent": "research-reproduction/1.0"}) as r:
                r.raise_for_status()
                with open(dest, "wb") as fh:
                    for chunk in r.iter_content(chunk_size=1 << 20):
                        fh.write(chunk)
            print(f"       saved {dest.stat().st_size / 1e6:.1f} MB")
        except Exception as exc:  # noqa: BLE001
            if dest.exists():
                dest.unlink()
            failed.append((key, src, exc))

    if failed:
        print("\nSome downloads failed. Download these by hand and save them in data/raw/:")
        for key, src, exc in failed:
            print(f"  - {key}: {exc}\n    page: {src['landing']}\n    save as: {src['local']}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
