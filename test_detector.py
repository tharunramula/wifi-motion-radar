"""Unit tests for the motion detector (run: python -m pytest)."""
import random

from wifi_radar.detector import MotionDetector


def test_calm_signal_reports_no_motion():
    d = MotionDetector()
    rng = random.Random(0)
    seen = False
    for _ in range(400):
        seen |= d.update(-55.0 + rng.gauss(0, 1.0)).motion
    assert not seen


def test_noisy_burst_triggers_motion():
    d = MotionDetector()
    rng = random.Random(1)
    for _ in range(300):  # settle the baseline
        d.update(-55.0 + rng.gauss(0, 1.0))
    seen = False
    for _ in range(120):  # simulated movement
        seen |= d.update(-55.0 + rng.gauss(0, 7.0)).motion
    assert seen


def test_motion_releases_after_calm_returns():
    d = MotionDetector()
    rng = random.Random(2)
    for _ in range(300):
        d.update(-55.0 + rng.gauss(0, 1.0))
    for _ in range(120):
        d.update(-55.0 + rng.gauss(0, 7.0))
    for _ in range(400):
        d.update(-55.0 + rng.gauss(0, 1.0))
    assert not d.motion
