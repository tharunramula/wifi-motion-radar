"""RSSI sample collection.

A real Wi-Fi "radar" reads Channel State Information (CSI) from the radio.
This demo instead watches Received Signal Strength (RSSI) fluctuations:
when someone moves near the access point or the sensing device, the
multipath environment changes and RSSI gets noisier. It's a heuristic,
not true radar -- but it demonstrates the full sensing pipeline.
"""
from __future__ import annotations

import random
import re
import subprocess
import time


class RSSISource:
    """Returns one RSSI sample in dBm, or None if unavailable."""

    def read_dbm(self) -> float | None:  # pragma: no cover - hardware
        raise NotImplementedError

    def describe(self) -> str:
        return type(self).__name__


class LinuxIwSource(RSSISource):
    """Reads RSSI via `iw dev <iface> link` (Linux)."""

    def __init__(self, interface: str | None = None):
        self.interface = interface or self._detect_interface()
        if not self.interface:
            raise RuntimeError("no wireless interface found (is Wi-Fi up?)")

    @staticmethod
    def _detect_interface() -> str | None:
        try:
            out = subprocess.run(
                ["iw", "dev"], capture_output=True, text=True, timeout=5
            ).stdout
        except (FileNotFoundError, subprocess.SubprocessError):
            return None
        m = re.search(r"Interface\s+(\S+)", out)
        return m.group(1) if m else None

    def read_dbm(self) -> float | None:
        try:
            out = subprocess.run(
                ["iw", "dev", self.interface, "link"],
                capture_output=True,
                text=True,
                timeout=5,
            ).stdout
        except (FileNotFoundError, subprocess.SubprocessError):
            return None
        m = re.search(r"signal:\s*(-?\d+)\s*dBm", out)
        return float(m.group(1)) if m else None

    def describe(self) -> str:
        return f"Linux iw on {self.interface}"


class ProcNetWirelessSource(RSSISource):
    """Fallback: parse /proc/net/wireless (link quality -> approx dBm)."""

    def read_dbm(self) -> float | None:
        try:
            with open("/proc/net/wireless") as fh:
                lines = fh.readlines()
        except OSError:
            return None
        for line in lines[2:]:
            parts = line.split()
            if len(parts) >= 4:
                try:
                    level = float(parts[3].rstrip("."))
                except ValueError:
                    continue
                return level - 256 if level > 0 else level  # driver quirk
        return None


class MacAirportSource(RSSISource):
    """Reads RSSI via the private `airport` tool (macOS)."""

    _AIRPORT = (
        "/System/Library/PrivateFrameworks/Apple80211.framework/"
        "Versions/Current/Resources/airport"
    )

    def read_dbm(self) -> float | None:
        try:
            out = subprocess.run(
                [self._AIRPORT, "-I"], capture_output=True, text=True, timeout=5
            ).stdout
        except (FileNotFoundError, subprocess.SubprocessError):
            return None
        m = re.search(r"agrCtlRSSI:\s*(-?\d+)", out)
        return float(m.group(1)) if m else None


class WindowsNetshSource(RSSISource):
    """Reads RSSI via `netsh wlan show interfaces` (Windows)."""

    def read_dbm(self) -> float | None:
        try:
            out = subprocess.run(
                ["netsh", "wlan", "show", "interfaces"],
                capture_output=True,
                text=True,
                timeout=5,
            ).stdout
        except (FileNotFoundError, subprocess.SubprocessError):
            return None
        m = re.search(r"Signal\s*:\s*(\d+)\s*%", out)
        if not m:
            return None
        pct = float(m.group(1))
        return (pct / 2) - 100  # rough % -> dBm mapping


class SimulatedSource(RSSISource):
    """Synthetic RSSI with random 'movement' bursts.

    Lets the demo run on any machine with no Wi-Fi hardware.
    """

    def __init__(self, base_dbm: float = -55.0, seed: int | None = None):
        self.base = base_dbm
        self.rng = random.Random(seed)
        self._motion_until = 0.0
        self._next_event = time.monotonic() + self.rng.uniform(8, 20)

    def read_dbm(self) -> float:
        now = time.monotonic()
        if now >= self._next_event:
            self._motion_until = now + self.rng.uniform(4, 9)
            self._next_event = now + self.rng.uniform(12, 30)
        moving = now < self._motion_until
        noise = self.rng.gauss(0.0, 6.0 if moving else 1.3)
        return self.base + noise

    def describe(self) -> str:
        return "simulated RSSI (no hardware)"


def auto_source(interface: str | None = None) -> RSSISource:
    """Pick the first working real source; raise RuntimeError if none works."""
    candidates = [
        lambda: LinuxIwSource(interface),
        ProcNetWirelessSource,
        MacAirportSource,
        WindowsNetshSource,
    ]
    last_err: Exception | None = None
    for make in candidates:
        try:
            src = make()
        except Exception as exc:  # noqa: BLE001 - trying next backend
            last_err = exc
            continue
        if src.read_dbm() is not None:
            return src
    raise RuntimeError(
        "could not read Wi-Fi signal on this machine"
        + (f" ({last_err})" if last_err else "")
        + " -- try --simulate"
    )
