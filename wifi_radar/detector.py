"""Motion detection from an RSSI stream.

Idea: a still room gives a stable RSSI (low short-term variance). A person
moving changes multipath reflections, making RSSI jumpy. We compare
short-window variance against a long-run baseline.
"""
from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass


@dataclass
class Reading:
    dbm: float
    motion: bool
    activity: float  # 0..100
    score: float


class MotionDetector:
    def __init__(
        self,
        short_window: int = 30,  # ~3 s at 10 Hz
        long_window: int = 300,  # ~30 s baseline
        threshold: float = 2.4,  # score above this => motion
        confirm: int = 4,  # consecutive hits to trigger
        release: int = 12,  # consecutive misses to release
    ):
        self.short: deque[float] = deque(maxlen=short_window)
        self.long: deque[float] = deque(maxlen=long_window)
        self.threshold = threshold
        self.confirm = confirm
        self.release = release
        self._hits = 0
        self._misses = 0
        self.motion = False

    @staticmethod
    def _std(values: deque[float]) -> float:
        n = len(values)
        if n < 2:
            return 0.0
        mean = sum(values) / n
        return math.sqrt(sum((v - mean) ** 2 for v in values) / n)

    def update(self, dbm: float) -> Reading:
        self.short.append(dbm)
        self.long.append(dbm)

        short_std = self._std(self.short)
        long_std = max(self._std(self.long), 0.8)  # floor avoids div-by-zero
        score = short_std / long_std if len(self.short) >= 10 else 0.0

        if score > self.threshold:
            self._hits += 1
            self._misses = 0
        else:
            self._misses += 1
            self._hits = 0

        if not self.motion and self._hits >= self.confirm:
            self.motion = True
        elif self.motion and self._misses >= self.release:
            self.motion = False

        activity = min(100.0, max(0.0, (score / self.threshold) * 50.0))
        return Reading(dbm=dbm, motion=self.motion, activity=activity, score=score)
