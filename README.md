# 🛢️ Cooking Oil IoT Simulator

A **FastAPI-based backend** that simulates an IoT device for monitoring cooking oil levels in a container. Features real-time SSE streaming, configurable simulation parameters, historical data storage, and a built-in web dashboard.

---

## ✨ Features

- **Real-time SSE streaming** of oil level data
- **Async simulation** with configurable drain rates
- **Automatic oil consumption** with random rates
- **Historical data storage** - fetch last N records
- **Built-in web dashboard** for monitoring and control
- **RESTful API** for full control and monitoring
- **Configurable settings** for capacity, drain rates, and intervals

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- pip

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/QuincyThawne/cooking-oil-iot-simulator.git
   cd cooking-oil-iot-simulator
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the server:**
   ```bash
   uvicorn main:app --reload --port 8000
   ```

4. **Access the application:**
   - **Web Dashboard**: http://localhost:8000
   - **API Documentation**: http://localhost:8000/docs
   - **ReDoc**: http://localhost:8000/redoc

---

## 📡 API Endpoints

### 1. `GET /` - Web Dashboard
Returns the built-in HTML dashboard for monitoring and controlling the simulation.

---

### 2. `GET /api/stream` - Real-time SSE Stream
Server-Sent Events endpoint for real-time oil level updates.

**Response (SSE):**
```json
{
  "timestamp": 1732189200,
  "device_id": "oil-sensor-001",
  "oil_level_ml": 850.5,
  "oil_percent": 85.05,
  "capacity_ml": 1000,
  "running": true
}
```

**Example (JavaScript):**
```javascript
const eventSource = new EventSource('http://localhost:8000/api/stream');
eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(`Oil Level: ${data.oil_level_ml}ml (${data.oil_percent}%)`);
};
```

---

### 3. `GET /api/state` - Get Current State
Returns current simulation state and settings.

**Response:**
```json
{
  "state": {
    "running": true,
    "oil_level_ml": 750.25,
    "capacity_ml": 1000,
    "last_update": 1732189200
  },
  "settings": {
    "drain_rate_min_ml": 1.0,
    "drain_rate_max_ml": 5.0,
    "update_interval_seconds": 2.0,
    "stop_on_empty": false
  }
}
```

**Example:**
```bash
curl http://localhost:8000/api/state
```

---

### 4. `POST /api/settings` - Update Settings
Modify simulation parameters.

**Request Body:**
```json
{
  "capacity_ml": 2000,
  "drain_rate_min_ml": 2.0,
  "drain_rate_max_ml": 8.0,
  "update_interval_seconds": 1.5,
  "stop_on_empty": true
}
```

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `capacity_ml` | float | Maximum container capacity |
| `drain_rate_min_ml` | float | Minimum oil removal per update |
| `drain_rate_max_ml` | float | Maximum oil removal per update |
| `update_interval_seconds` | float | Time between updates |
| `stop_on_empty` | boolean | Stop simulation when empty |

**Example:**
```bash
curl -X POST http://localhost:8000/api/settings \
  -H "Content-Type: application/json" \
  -d '{"drain_rate_min_ml": 2.0, "drain_rate_max_ml": 10.0}'
```

---

### 5. `POST /api/control` - Control Simulation
Start, stop, or refill the container.

**Request Body:**
```json
{
  "cmd": "start"  // "start", "stop", or "refill"
}
```

**Commands:**
| Command | Description |
|---------|-------------|
| `start` | Begin oil consumption simulation |
| `stop` | Pause the simulation |
| `refill` | Reset oil level to maximum capacity |

**Examples:**
```bash
# Start simulation
curl -X POST http://localhost:8000/api/control \
  -H "Content-Type: application/json" \
  -d '{"cmd": "start"}'

# Stop simulation
curl -X POST http://localhost:8000/api/control \
  -H "Content-Type: application/json" \
  -d '{"cmd": "stop"}'

# Refill container
curl -X POST http://localhost:8000/api/control \
  -H "Content-Type: application/json" \
  -d '{"cmd": "refill"}'
```

---

### 6. `GET /api/device-info` - Device Information
Returns simulated IoT device details.

**Response:**
```json
{
  "device_id": "oil-sensor-001",
  "model": "KitchenOilMonitor v1",
  "firmware": "1.0.0"
}
```

**Example:**
```bash
curl http://localhost:8000/api/device-info
```

---

### 7. `GET /api/history` - Historical Data
Fetch the last N records from the stream.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `n` | int | 10 | Number of records to fetch (1-1000) |

**Response:**
```json
{
  "ok": true,
  "count": 10,
  "requested": 10,
  "total_available": 245,
  "records": [
    {
      "timestamp": 1732189200,
      "device_id": "oil-sensor-001",
      "oil_level_ml": 850.5,
      "oil_percent": 85.05,
      "capacity_ml": 1000,
      "running": true
    }
  ]
}
```

**Examples:**
```bash
# Get last 10 records (default)
curl http://localhost:8000/api/history

# Get last 50 records
curl "http://localhost:8000/api/history?n=50"

# Get last 100 records
curl "http://localhost:8000/api/history?n=100"
```

---

## 🔧 Configuration

### Default Settings

| Setting | Default Value | Description |
|---------|---------------|-------------|
| `capacity_ml` | 1000 | Container capacity in milliliters |
| `drain_rate_min_ml` | 1.0 | Minimum drain per tick |
| `drain_rate_max_ml` | 5.0 | Maximum drain per tick |
| `update_interval_seconds` | 2.0 | Update frequency |
| `stop_on_empty` | false | Auto-stop when empty |

---

## 🧪 Testing the API

### Using the Web Dashboard
Visit http://localhost:8000 to use the built-in dashboard with:
- Real-time oil level visualization
- Control buttons (Start/Stop/Refill)
- Settings configuration panel

### Using curl
```bash
# 1. Check device info
curl http://localhost:8000/api/device-info

# 2. Get current state
curl http://localhost:8000/api/state

# 3. Start simulation
curl -X POST http://localhost:8000/api/control \
  -H "Content-Type: application/json" \
  -d '{"cmd": "start"}'

# 4. Get historical data
curl "http://localhost:8000/api/history?n=20"

# 5. Update settings
curl -X POST http://localhost:8000/api/settings \
  -H "Content-Type: application/json" \
  -d '{"drain_rate_max_ml": 10.0}'

# 6. Refill container
curl -X POST http://localhost:8000/api/control \
  -H "Content-Type: application/json" \
  -d '{"cmd": "refill"}'
```

### Using Python
```python
import requests

BASE_URL = "http://localhost:8000"

# Get device info
response = requests.get(f"{BASE_URL}/api/device-info")
print(response.json())

# Start simulation
requests.post(f"{BASE_URL}/api/control", json={"cmd": "start"})

# Get state
response = requests.get(f"{BASE_URL}/api/state")
print(response.json())

# Get last 20 records
response = requests.get(f"{BASE_URL}/api/history", params={"n": 20})
print(response.json())

# Refill
requests.post(f"{BASE_URL}/api/control", json={"cmd": "refill"})
```

---

## 📁 Project Structure

```
cooking-oil-iot-simulator/
├── main.py              # Main FastAPI application
├── requirements.txt     # Python dependencies
├── render.yaml          # Render deployment config
├── start.sh             # Startup script
└── README.md            # This file
```

---

## 🚢 Deployment

### Deploy to Render
This project includes a `render.yaml` for easy deployment to [Render](https://render.com).

1. Connect your GitHub repository to Render
2. Render will automatically detect the configuration
3. Deploy!

### Manual Deployment
```bash
# Production run
uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Change port
uvicorn main:app --port 8080
```

### SSE Connection Issues
- Ensure browser supports Server-Sent Events
- Check firewall settings
- Use curl or EventSource API correctly

---

## 📝 License

MIT License - feel free to use for educational and commercial purposes.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

---

**Built with FastAPI 🚀 | Powered by Python 🐍**
