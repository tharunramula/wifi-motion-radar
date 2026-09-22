"""Live terminal dashboard (ANSI, no dependencies)."""
from __future__ import annotations

import sys

BLOCKS = " ▁▂▃▄▅▆▇█"


def sparkline(values: list[float], width: int = 60,
              lo: float = -80.0, hi: float = -30.0) -> str:
    vals = values[-width:]
    out = []
    for v in vals:
        frac = min(1.0, max(0.0, (v - lo) / (hi - lo)))
        out.append(BLOCKS[int(frac * (len(BLOCKS) - 1))])
    return "".join(out)


def _bar(pct: float, width: int = 30) -> str:
    fill = int(pct / 100 * width)
    return "█" * fill + "░" * (width - fill)


class TerminalDashboard:
    def __init__(self, width: int = 60):
        self.width = width
        self.history: list[float] = []

    def render(self, reading, source_desc: str, elapsed: float,
               threshold: float) -> None:
        self.history.append(reading.dbm)
        status = (
            "\033[91m● MOTION DETECTED\033[0m"
            if reading.motion
            else "\033[92m● calm\033[0m"
        )
        lines = [
            "\033[2J\033[H",
            "  WiFi Motion Radar  (demo -- RSSI fluctuation sensing)",
            f"  source: {source_desc}   elapsed: {elapsed:.0f}s",
            "",
            f"  signal   {reading.dbm:6.1f} dBm",
            f"  {sparkline(self.history, self.width)}",
            "",
            f"  status   {status}",
            f"  activity {_bar(reading.activity)} {reading.activity:5.1f}%",
            f"  score    {reading.score:5.2f}  (threshold {threshold})",
            "",
            "  Ctrl+C to quit",
        ]
        sys.stdout.write("\n".join(lines))
        sys.stdout.flush()
