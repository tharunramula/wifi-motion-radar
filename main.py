#!/usr/bin/env python3
"""wifi-motion-radar: demo Wi-Fi motion sensing from RSSI fluctuations.

Usage:
    python main.py --simulate          # no Wi-Fi hardware needed
    python main.py                     # try real Wi-Fi, fall back to simulate
    python main.py --simulate --web    # browser dashboard at localhost:5000
"""
from __future__ import annotations

import argparse
import time

from wifi_radar.collector import SimulatedSource, auto_source
from wifi_radar.dashboard import TerminalDashboard
from wifi_radar.detector import MotionDetector


def main() -> None:
    ap = argparse.ArgumentParser(description="Demo Wi-Fi motion radar")
    ap.add_argument("--simulate", action="store_true",
                    help="use synthetic RSSI (no Wi-Fi hardware needed)")
    ap.add_argument("--interface", default=None,
                    help="wireless interface (Linux iw backend)")
    ap.add_argument("--rate", type=float, default=10.0,
                    help="samples per second (default 10)")
    ap.add_argument("--web", action="store_true",
                    help="serve a web dashboard instead of terminal UI")
    ap.add_argument("--port", type=int, default=5000)
    args = ap.parse_args()

    if args.simulate:
        source = SimulatedSource()
    else:
        try:
            source = auto_source(args.interface)
        except RuntimeError as exc:
            print(f"Note: {exc}\nFalling back to --simulate mode.\n")
            source = SimulatedSource()
    print(f"Source: {source.describe()}")

    detector = MotionDetector()
    interval = 1.0 / args.rate

    if args.web:
        try:
            from wifi_radar.web import run_web
        except ImportError:
            raise SystemExit("web mode needs flask: pip install flask")
        run_web(source, detector, port=args.port, rate=args.rate)
        return

    dash = TerminalDashboard()
    start = time.monotonic()
    try:
        while True:
            dbm = source.read_dbm()
            if dbm is not None:
                reading = detector.update(dbm)
                dash.render(reading, source.describe(),
                            time.monotonic() - start, detector.threshold)
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
