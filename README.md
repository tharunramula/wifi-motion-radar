# WiFi Motion Radar (demo)

A Python demo of **Wi-Fi sensing**: detecting movement in a room by watching
fluctuations in the Wi-Fi signal -- the same core idea behind real Wi-Fi radar.

## How it works

Real Wi-Fi sensing reads **Channel State Information (CSI)** -- fine-grained
measurements of how the radio signal is distorted as it bounces around a room.
When a person moves, the multipath reflections change, and the signal gets
"jumpy". (This is now an official IEEE standard: **802.11bf**.)

This demo implements the same *pipeline* with a simpler input: **RSSI**
(received signal strength, in dBm), which any laptop can read without special
hardware:

```
Wi-Fi radio  ->  RSSI sampler  ->  motion detector  ->  live dashboard
   (collector)      (detector)         (dashboard)
```

The detector compares **short-term signal variance** (~3 s window) against a
**long-term baseline** (~30 s). A still room = stable RSSI. A moving person =
noisy RSSI. When the ratio crosses a threshold for a few consecutive samples,
it reports **MOTION DETECTED**.

## Honest limitations

This is a *demo of the concept*, not true radar:

- RSSI is a coarse, 1-dimensional signal. It can't tell you *where* someone
  is, how many people there are, or distinguish a person from a microwave.
- Real Wi-Fi radar needs CSI data (ESP32, Intel 5300 with patched firmware,
  or 802.11bf-capable hardware) and ML models on top.
- It only senses movement *near the radio path* -- between your device and
  the access point, or close to the sensing device.

## Quickstart

No dependencies for the core demo (Python 3.10+):

```bash
# Simulated mode -- works on ANY machine, no Wi-Fi hardware needed
python main.py --simulate

# Real mode -- reads your actual Wi-Fi signal (Linux/macOS/Windows),
# falls back to simulation if no radio is readable
python main.py

# Web dashboard instead of terminal UI (needs: pip install flask)
python main.py --simulate --web
# then open http://127.0.0.1:5000
```

Watch the terminal: every ~15-30 seconds the simulator injects a "movement"
burst and you should see the status flip to **MOTION DETECTED**.

## Running the tests

```bash
python -m pytest
```

## Project layout

```
wifi-motion-radar/
├── main.py                 # CLI entry point
├── wifi_radar/
│   ├── collector.py        # RSSI backends: Linux(iw), macOS, Windows, simulator
│   ├── detector.py         # variance-ratio motion detection
│   ├── dashboard.py        # live terminal UI (ANSI, no deps)
│   └── web.py              # optional Flask + Chart.js web UI
├── tests/
│   └── test_detector.py
└── requirements.txt        # flask (optional, for --web)
```

## Going further (real Wi-Fi radar)

To build the *real* version, you need CSI-capable hardware:

1. **ESP32** (~$10) running Espressif's `esp-csi` example -- streams CSI
   frames over serial/MQTT.
2. A Python service replacing `collector.py` that ingests CSI amplitude
   instead of RSSI (the `detector.py` variance logic still applies as a
   first pass).
3. For production accuracy: train a small classifier (random forest / CNN)
   on labeled still-vs-moving CSI captures.

## License

MIT -- see [LICENSE](LICENSE).
