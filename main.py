"""
Smart Oil Simulator - single-file FastAPI app

Save this file as `smart_oil_simulator.py` and run:

    pip install fastapi uvicorn
    uvicorn smart_oil_simulator:app --reload --port 8000

Open http://127.0.0.1:8000/ in your browser.

This app provides:
- SSE stream at /api/stream
- GET /api/state
- POST /api/settings
- POST /api/control (start/stop/refill)
- GET /api/device-info

Frontend is embedded and served at /
"""

import asyncio
import json
import random
import time
from collections import deque
from fastapi import FastAPI, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from typing import Dict, Optional

app = FastAPI(title="Smart Oil IoT Simulator")

# Enable CORS for all origins (allows React frontend to access the API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],  # Allows all headers
)

# --- Device & simulation state ---
DEVICE_ID = "oil-sensor-001"
DEVICE_INFO = {
    "device_id": DEVICE_ID,
    "model": "KitchenOilMonitor v1",
    "firmware": "1.0.0"
}

state = {
    "running": True,
    "oil_level_ml": 1000.0,      # current oil in milliliters
    "capacity_ml": 1000.0,       # max capacity
    "last_update": time.time(),
}

# Default simulation settings
settings = {
    "drain_rate_min_ml": 1.0,    # minimum removed per tick
    "drain_rate_max_ml": 5.0,    # maximum removed per tick
    "update_interval_seconds": 2.0,
    "stop_on_empty": False       # if True, auto-stop when 0
}

# Historical data storage (stores last 1000 records)
historical_data = deque(maxlen=1000)

# clamp helper
def clamp(v, a, b):
    return max(a, min(b, v))

# SSE event generator
async def event_generator():
    """Yield Server-Sent Events with current oil level."""
    while True:
        if state["running"]:
            # choose drain amount
            drain = random.uniform(settings["drain_rate_min_ml"], settings["drain_rate_max_ml"])
            # subtract but never below zero
            new_level = max(0.0, state["oil_level_ml"] - drain)
            state["oil_level_ml"] = round(new_level, 2)
            state["last_update"] = time.time()

            # if empty and configured to stop, stop
            if state["oil_level_ml"] <= 0 and settings.get("stop_on_empty"):
                state["running"] = False

        payload = {
            "timestamp": int(time.time()),
            "device_id": DEVICE_ID,
            "oil_level_ml": state["oil_level_ml"],
            "oil_percent": round((state["oil_level_ml"] / state["capacity_ml"]) * 100.0, 2),
            "capacity_ml": state["capacity_ml"],
            "running": state["running"]
        }
        # Store in historical data
        historical_data.append(payload.copy())
        yield f"data: {json.dumps(payload)}\n\n"
        await asyncio.sleep(max(0.1, float(settings.get("update_interval_seconds", 1.0))))

# --- Routes ---
@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    html = HTML_PAGE
    return HTMLResponse(content=html)

@app.get("/api/stream")
async def stream():
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/api/state")
async def get_state():
    return JSONResponse({"state": state, "settings": settings})

@app.post("/api/settings")
async def post_settings(payload: Dict):
    # whitelist updateable keys
    allowed = {"drain_rate_min_ml", "drain_rate_max_ml", "update_interval_seconds", "capacity_ml", "stop_on_empty"}
    for k, v in payload.items():
        if k in allowed:
            try:
                if k == "stop_on_empty":
                    settings[k] = bool(v)
                else:
                    settings[k] = float(v)
            except Exception:
                pass
    # if capacity changed, adjust state capacity and clamp current level
    if "capacity_ml" in payload:
        cap = float(payload["capacity_ml"]) if payload.get("capacity_ml") is not None else state["capacity_ml"]
        state["capacity_ml"] = cap
        state["oil_level_ml"] = clamp(state.get("oil_level_ml", 0.0), 0.0, cap)

    # ensure min <= max
    if settings["drain_rate_min_ml"] > settings["drain_rate_max_ml"]:
        settings["drain_rate_min_ml"], settings["drain_rate_max_ml"] = settings["drain_rate_max_ml"], settings["drain_rate_min_ml"]

    return JSONResponse({"ok": True, "settings": settings})

@app.post("/api/control")
async def control(payload: Dict):
    cmd = (payload.get("cmd") or "").lower()
    if cmd == "start":
        state["running"] = True
    elif cmd == "stop":
        state["running"] = False
    elif cmd == "refill":
        # refill to capacity
        cap = state.get("capacity_ml", 1000.0)
        state["oil_level_ml"] = float(cap)
        state["last_update"] = time.time()
    else:
        return JSONResponse({"ok": False, "error": "unknown cmd"}, status_code=400)
    return JSONResponse({"ok": True, "state": state})

@app.get("/api/device-info")
async def device_info():
    return JSONResponse(DEVICE_INFO)

@app.get("/api/history")
async def get_history(n: Optional[int] = Query(default=10, ge=1, le=1000, description="Number of records to fetch")):
    """
    Fetch the last n records from the historical data.
    Parameters:
        n: Number of records to return (default: 10, max: 1000)
    Returns:
        List of historical oil level records
    """
    # Get last n records
    records = list(historical_data)
    last_n = records[-n:] if len(records) >= n else records
    
    return JSONResponse({
        "ok": True,
        "count": len(last_n),
        "requested": n,
        "total_available": len(records),
        "records": last_n
    })

# --- Embedded frontend (HTML + CSS + JS) ---
HTML_PAGE = r'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Oil Level IoT Simulator</title>
  <style>
    :root{--bg:#071026;--card:#0b1220;--accent:#f59e0b;--muted:#94a3b8}
    *{box-sizing:border-box;font-family:Inter,ui-sans-serif,system-ui,-apple-system,'Segoe UI',Roboto,'Helvetica Neue',Arial;color:#e6eef8}
    body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;background:linear-gradient(180deg,#031124,#071a2a)}
    .app{width:95%;max-width:1000px;padding:20px}
    h1{color:var(--accent);margin:0 0 12px 0}
    .layout{display:flex;gap:20px}
    .panel{background:rgba(255,255,255,0.03);padding:16px;border-radius:12px;box-shadow:0 8px 30px rgba(0,0,0,0.6)}
    .device{width:360px;padding:20px;text-align:center}
    .gauge{width:220px;height:220px;border-radius:110px;background:linear-gradient(180deg,rgba(255,255,255,0.02),transparent);display:flex;align-items:center;justify-content:center;margin:0 auto 12px}
    .val{font-size:28px;font-weight:700}
    .small{font-size:14px;color:var(--muted)}
    .controls{flex:1;min-width:360px;padding:16px}
    label{display:block;margin:8px 0}
    input[type=number]{width:100%;padding:8px;border-radius:8px;border:none;background:rgba(255,255,255,0.02);color:inherit}
    .row{display:flex;gap:8px}
    button{padding:8px 12px;border-radius:8px;border:0;background:linear-gradient(180deg,#f59e0b,#b45309);color:#072024;font-weight:700;cursor:pointer}
    .muted{color:var(--muted);font-size:13px}
    footer{margin-top:12px;color:var(--muted);font-size:13px}
  </style>
</head>
<body>
  <div class="app">
    <h1>Cooking Oil IoT Simulator</h1>
    <div class="layout">
      <div class="panel device">
        <div class="gauge" id="gauge">
          <div>
            <div class="val" id="oil_ml">-- ml</div>
            <div class="small" id="oil_pct">-- %</div>
          </div>
        </div>
        <div class="small" id="status">connecting...</div>
        <div class="muted" id="last">-</div>
      </div>

      <div class="panel controls">
        <h3>Settings</h3>
        <label>Container capacity (ml)
          <input id="capacity" type="number" step="1" />
        </label>
        <div class="row">
          <div style="flex:1">
            <label>Drain min (ml)</label>
            <input id="drain_min" type="number" step="0.1" />
          </div>
          <div style="flex:1">
            <label>Drain max (ml)</label>
            <input id="drain_max" type="number" step="0.1" />
          </div>
        </div>
        <label>Update interval (s)
          <input id="interval" type="number" step="0.1" />
        </label>
        <label><input id="stop_on_empty" type="checkbox" /> Stop on empty</label>

        <div style="margin-top:10px;display:flex;gap:8px">
          <button id="apply">Apply</button>
          <button id="refill">Refill</button>
          <button id="start">Start</button>
          <button id="stop">Stop</button>
        </div>

        <hr />
        <div class="muted">API endpoints: <code>/api/stream</code> (SSE), <code>/api/state</code>, <code>/api/history</code>, <code>/api/history?n=1</code></div>
      </div>
    </div>
    <footer>Device: <span id="deviceid">-</span> • <span id="fw">-</span></footer>
  </div>

<script>
  const oilEl = document.getElementById('oil_ml');
  const pctEl = document.getElementById('oil_pct');
  const statusEl = document.getElementById('status');
  const lastEl = document.getElementById('last');
  const deviceEl = document.getElementById('deviceid');
  const fwEl = document.getElementById('fw');

  const capacityInput = document.getElementById('capacity');
  const drainMinInput = document.getElementById('drain_min');
  const drainMaxInput = document.getElementById('drain_max');
  const intervalInput = document.getElementById('interval');
  const stopOnEmptyInput = document.getElementById('stop_on_empty');

  const applyBtn = document.getElementById('apply');
  const refillBtn = document.getElementById('refill');
  const startBtn = document.getElementById('start');
  const stopBtn = document.getElementById('stop');

  let es;
  function connect() {
    es = new EventSource('/api/stream');
    es.onopen = () => { statusEl.textContent = 'connected'; }
    es.onerror = () => { statusEl.textContent = 'disconnected'; }
    es.onmessage = (e) => {
      const d = JSON.parse(e.data);
      oilEl.textContent = d.oil_level_ml.toFixed(2) + ' ml';
      pctEl.textContent = d.oil_percent + ' %';
      statusEl.textContent = d.running ? 'running' : 'stopped';
      lastEl.textContent = 'updated ' + new Date(d.timestamp * 1000).toLocaleTimeString();
    };
  }

  async function loadState(){
    const r = await fetch('/api/state');
    const j = await r.json();
    const s = j.settings;
    const st = j.state;
    capacityInput.value = st.capacity_ml || s.get('capacity_ml') || 1000;
    drainMinInput.value = s.drain_rate_min_ml;
    drainMaxInput.value = s.drain_rate_max_ml;
    intervalInput.value = s.update_interval_seconds;
    stopOnEmptyInput.checked = !!s.stop_on_empty;
  }

  async function loadDevice(){
    const r = await fetch('/api/device-info');
    const j = await r.json();
    deviceEl.textContent = j.device_id;
    fwEl.textContent = j.model + ' • fw ' + j.firmware;
  }

  applyBtn.addEventListener('click', async () => {
    const payload = {
      capacity_ml: parseFloat(capacityInput.value),
      drain_rate_min_ml: parseFloat(drainMinInput.value),
      drain_rate_max_ml: parseFloat(drainMaxInput.value),
      update_interval_seconds: parseFloat(intervalInput.value),
      stop_on_empty: stopOnEmptyInput.checked
    };
    await fetch('/api/settings', {method: 'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
    alert('Settings applied');
  });

  refillBtn.addEventListener('click', async () => {
    await fetch('/api/control', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({cmd:'refill'})});
  });
  startBtn.addEventListener('click', async () => {
    await fetch('/api/control', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({cmd:'start'})});
  });
  stopBtn.addEventListener('click', async () => {
    await fetch('/api/control', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({cmd:'stop'})});
  });

  // init
  loadState();
  loadDevice();
  connect();
</script>
</body>
</html>
'''
