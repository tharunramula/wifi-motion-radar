"""Optional web dashboard:  python main.py --simulate --web  (needs flask)."""
from __future__ import annotations

import json
import threading
import time
from collections import deque

HTML = """<!doctype html>
<html><head><title>WiFi Motion Radar</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
body{font-family:system-ui;background:#111;color:#eee;margin:0;padding:24px}
#status{font-size:28px;margin:12px 0}
.motion{color:#ff5555}.calm{color:#55ff88}
canvas{background:#1a1a1a;border-radius:8px;max-height:50vh}
</style></head><body>
<h1>WiFi Motion Radar <small style="color:#888">(demo)</small></h1>
<div id="status" class="calm">&#9679; calm</div>
<canvas id="c"></canvas>
<script>
const ctx=document.getElementById('c').getContext('2d');
const chart=new Chart(ctx,{type:'line',
 data:{labels:[],datasets:[{label:'RSSI (dBm)',data:[],borderColor:'#4da3ff',pointRadius:0,tension:0.3}]},
 options:{animation:false,scales:{y:{min:-80,max:-30}}}});
const es=new EventSource('/stream');
es.onmessage=e=>{const d=JSON.parse(e.data);
 chart.data.labels.push('');chart.data.datasets[0].data.push(d.dbm);
 if(chart.data.labels.length>300){chart.data.labels.shift();chart.data.datasets[0].data.shift();}
 chart.update('none');
 const s=document.getElementById('status');
 s.className=d.motion?'motion':'calm';
 s.innerHTML='&#9679; '+(d.motion?'MOTION DETECTED':'calm');};
</script></body></html>"""


def run_web(source, detector, port: int = 5000, rate: float = 10.0) -> None:
    from flask import Flask, Response

    app = Flask(__name__)
    buf: deque[dict] = deque(maxlen=300)

    def sampler() -> None:
        while True:
            dbm = source.read_dbm()
            if dbm is not None:
                r = detector.update(dbm)
                buf.append({
                    "t": time.time(), "dbm": r.dbm,
                    "motion": r.motion, "activity": r.activity,
                })
            time.sleep(1.0 / rate)

    threading.Thread(target=sampler, daemon=True).start()

    @app.route("/")
    def index():
        return HTML

    @app.route("/stream")
    def stream():
        def gen():
            last = 0
            while True:
                while len(buf) > last:
                    yield f"data: {json.dumps(buf[last])}\n\n"
                    last += 1
                time.sleep(0.1)

        return Response(gen(), mimetype="text/event-stream")

    print(f"Web dashboard at http://127.0.0.1:{port}  (Ctrl+C to quit)")
    app.run(port=port)
