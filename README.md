# ♻️ Recycling Robotic Arm — Control Interface & Vision System

A full-stack robotics operations dashboard and vision pipeline for an automated recycling robotic arm. The system combines **real-time YOLO-based bottle detection** via webcam, a low-latency **WebSocket video & telemetry streaming server** built with FastAPI, an **ESP32 microcontroller serial interface** for hardware control, and a responsive **Next.js operations console**.

---

## 📑 Table of Contents

- [Overview & Capabilities](#-overview--capabilities)
- [System Architecture](#-system-architecture)
- [Repository Structure](#-repository-structure)
- [Prerequisites](#-prerequisites)
- [Quick Start Guide](#-quick-start-guide)
- [Step-by-Step Setup](#-step-by-step-setup)
  - [1. Backend Setup (FastAPI & YOLO)](#1-backend-setup-fastapi--yolo)
  - [2. Frontend Setup (Next.js Dashboard)](#2-frontend-setup-nextjs-dashboard)
  - [3. ESP32 Firmware & Hardware Setup (Optional)](#3-esp32-firmware--hardware-setup-optional)
- [How to Start and Run the Application](#-how-to-start-and-run-the-application)
- [Using the Dashboard](#-using-the-dashboard)
- [Communication & Hardware Protocols](#-communication--hardware-protocols)
  - [WebSocket Protocol (`/ws`)](#websocket-protocol-ws)
  - [ESP32 Serial Protocol](#esp32-serial-protocol)
- [API Reference](#-api-reference)
- [Environment Variables](#-environment-variables)
- [Troubleshooting & Common Issues](#-troubleshooting--common-issues)
- [Production Deployment](#-production-deployment)

---

## 🌟 Overview & Capabilities

| Subsystem | Technologies | Functionality |
| :--- | :--- | :--- |
| **Frontend UI** | Next.js 15, React 19, Tailwind CSS, TypeScript, Lucide Icons | Real-time operations dashboard, live camera feed, detection confidence gauges, device connectivity monitors |
| **Backend API** | FastAPI, Uvicorn, Python 3.12, asyncio | Asynchronous REST API, WebSocket server for binary frame streaming and JSON telemetry snapshots |
| **Vision & AI** | Ultralytics YOLO (`yolo26n.pt`), OpenCV (DirectShow) | Real-time bottle presence detection, dynamic bounding box rendering, frame encoding |
| **Hardware Link** | pySerial, ESP32 DevKit, ESP32Servo | Thread-safe newline-delimited JSON serial protocol over USB for microcontroller telemetry and servo actuation |

### 🔒 Design Decoupling & Safety Limits
- **Independent Resources:** The camera and serial interfaces are completely decoupled. The application will start and function normally even if no webcam or ESP32 is physically connected.
- **Presence vs. Fill-Level Classification:** YOLO detects COCO class `bottle` presence and confidence. Fill-state classification is deliberately isolated and reports as `uncertain` until a dedicated fill-level sensor/model is integrated (transparency is never assumed to mean empty).
- **Safe Robot Controls:** Arm motion commands are disabled in the backend and frontend while mechanical arm prototyping is underway. Only non-motion diagnostics (`PING`, `GET_STATUS`) are permitted.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          USER BROWSER / CLIENT UI                               │
│                         http://localhost:3000                                   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────────────────────┐  │
│  │   Camera Panel   │  │  Classification  │  │   System & ESP32 Status Chips │  │
│  │ (Live JPEG feed) │  │  (Confidence %)  │  │  (Connected / Disconnected)   │  │
│  └────────▲─────────┘  └────────▲─────────┘  └───────────────▲───────────────┘  │
└───────────┼─────────────────────┼────────────────────────────┼──────────────────┘
            │ Binary JPEGs        │ JSON Status Telemetry      │ REST HTTP Calls
            │ (WebSocket)         │ (WebSocket)                │ (GET/POST)
┌───────────┴─────────────────────┴────────────────────────────┴──────────────────┐
│                         FASTAPI BACKEND SERVICE                                 │
│                          http://localhost:8000                                  │
│                                                                                 │
│   ┌────────────────────────┐      ┌─────────────────────────┐                   │
│   │     CameraManager      │◄────►│  BottleDetectionService │                   │
│   │  (OpenCV / DirectShow) │      │   (Ultralytics YOLO)    │                   │
│   └────────────────────────┘      └─────────────────────────┘                   │
│                                                                                 │
│   ┌────────────────────────┐      ┌─────────────────────────┐                   │
│   │    WebSocketManager    │      │      SerialManager      │                   │
│   │   (/ws client sync)    │      │  (Thread-Safe pySerial) │                   │
│   └────────────────────────┘      └────────────┬────────────┘                   │
└────────────────────────────────────────────────┼────────────────────────────────┘
                                                 │ USB Serial (115200 baud)
                                                 │ Newline-delimited JSON
                                                 ▼
                                    ┌────────────────────────┐
                                    │    ESP32 DEV MODULE    │
                                    │  (Firmware / Servos)   │
                                    └────────────────────────┘
```

---

## 📁 Repository Structure

```
Robotic_interface/
├── README.md                           # Main project documentation (this file)
│
├── backend/                            # FastAPI backend & vision pipeline
│   ├── .venv/                          # Python virtual environment (ignored in git)
│   ├── firmware/                       # Embedded C++ / Arduino sketches
│   │   └── recycling_arm_esp32/
│   │       └── recycling_arm_esp32.ino # ESP32 Arduino firmware sketch
│   ├── .env                            # Active backend environment settings
│   ├── .env.example                    # Template for backend settings
│   ├── .gitignore                      # Python & venv ignore rules
│   ├── camera.py                       # Thread-safe OpenCV camera manager
│   ├── detection.py                    # Ultralytics YOLO bottle detection service
│   ├── errors.py                       # Structured hardware error definitions
│   ├── main.py                         # FastAPI routes, lifespan, & WebSocket handler
│   ├── README.md                       # Backend-specific documentation
│   ├── requirements.txt                # Python dependencies
│   ├── serial_manager.py               # Serial protocol manager for ESP32
│   ├── websocket_manager.py            # Client connection & broadcast manager
│   └── yolo26n.pt                      # Pretrained YOLO model weights
│
└── frontend/                           # Next.js web operations console
    ├── src/
    │   ├── app/
    │   │   ├── globals.css             # Theme, animations, & dashboard styling
    │   │   ├── layout.tsx              # Root HTML shell & metadata
    │   │   └── page.tsx                # Main operations dashboard page
    │   ├── components/
    │   │   ├── camera/                 # Live video panel & Start/Stop controls
    │   │   ├── controls/               # Robotic arm status & safety interlocks
    │   │   ├── dashboard/              # Metrics, classification, and event logs
    │   │   ├── layout/                 # Sidebar and top navigation bar
    │   │   ├── realtime/               # WebSocket provider & stream state hook
    │   │   └── status/                 # Connectivity chips & badges
    │   ├── lib/
    │   │   ├── api.ts                  # Typed REST fetch helper
    │   │   └── websocket.ts            # WebSocket connection factory
    │   └── types/
    │       └── index.ts                # TypeScript interfaces for telemetry & errors
    ├── .env.example                    # Frontend environment template
    ├── .env.local                      # Active frontend environment settings
    ├── package.json                    # Node dependencies & npm scripts
    ├── tsconfig.json                   # TypeScript compiler configuration
    └── README.md                       # Frontend-specific documentation
```

---

## 🧰 Prerequisites

Before setting up the project, verify that the following dependencies are installed on your host system:

| Tool | Recommended Version | Verification Command | Notes |
| :--- | :--- | :--- | :--- |
| **Python** | 3.12+ (64-bit) | `python --version` | Required for FastAPI, OpenCV, and PyTorch |
| **Node.js** | 18.x or 20.x+ (LTS) | `node --version` | Required for Next.js 15 |
| **npm** | 9.x or 10.x+ | `npm --version` | Bundled with Node.js |
| **Git** | 2.x+ | `git --version` | Version control |
| **Arduino IDE** | 2.3+ *(Optional)* | — | Only needed if flashing ESP32 firmware |

### Hardware Prerequisites (Optional)
- **Webcam:** Any built-in laptop camera or standard USB UVC webcam.
- **ESP32 Board:** ESP32 DevKit V1 (with CP2102 or CH340 USB-to-UART chip).
- **Servo Motor:** Standard 50Hz PWM servo (e.g., SG90 or MG996R) wired to ESP32 **GPIO 26**.

---

## ⚡ Quick Start Guide

For developers on Windows who already have dependencies installed:

```powershell
# 1. Open Terminal 1: Start Backend
cd d:\Robotic_Arm\Robotic_interface\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env -Force
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 2. Open Terminal 2: Start Frontend
cd d:\Robotic_Arm\Robotic_interface\frontend
npm install
Copy-Item .env.example .env.local -Force
npm run dev

# 3. Open your browser
# Dashboard: http://localhost:3000
# API Docs:  http://localhost:8000/docs
```

---

## 🔨 Step-by-Step Setup

### 1. Backend Setup (FastAPI & YOLO)

#### Step 1.1 — Navigate to the backend directory
```powershell
cd d:\Robotic_Arm\Robotic_interface\backend
```

#### Step 1.2 — Create a Python Virtual Environment
```powershell
python -m venv .venv
```

#### Step 1.3 — Activate the Virtual Environment
- **Windows (PowerShell):**
  ```powershell
  .\.venv\Scripts\Activate.ps1
  ```
  *(If you encounter a script execution restriction, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first).*
- **Windows (CMD):**
  ```cmd
  .venv\Scripts\activate.bat
  ```
- **macOS / Linux:**
  ```bash
  source .venv/bin/activate
  ```

#### Step 1.4 — Install Dependencies
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```
> **Note:** Ultralytics pulls in PyTorch and OpenCV. On first run, it installs all computer vision dependencies. The local weights file `yolo26n.pt` is already bundled with the project.

#### Step 1.5 — Configure Environment Variables
Copy the template into an active `.env` file:
```powershell
Copy-Item .env.example .env
```
Edit `.env` using your editor of choice:
- Set `SERIAL_PORT` to your ESP32's COM port (e.g., `COM3`, `COM7`).
- Set `CAMERA_INDEX=0` (0 is typically the default laptop webcam).
- Leave `CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000`.

---

### 2. Frontend Setup (Next.js Dashboard)

#### Step 2.1 — Navigate to the frontend directory
Open a second terminal window and enter:
```powershell
cd d:\Robotic_Arm\Robotic_interface\frontend
```

#### Step 2.2 — Install Node Modules
```powershell
npm install
```

#### Step 2.3 — Configure Environment Variables
Copy the example environment file:
```powershell
Copy-Item .env.example .env.local
```
Verify `frontend/.env.local` contains:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

---

### 3. ESP32 Firmware & Hardware Setup (Optional)

If you have an ESP32 board and servo motor:

#### Wiring Table
| ESP32 DevKit Pin | Servo Motor Wire | Function |
| :--- | :--- | :--- |
| **GPIO 26** | Orange / Yellow | PWM Signal |
| **GND** | Brown / Black | Ground |
| **5V / VIN** | Red | Power *(use external 5V supply if driving multiple servos)* |

#### Flashing Firmware via Arduino IDE
1. Open **Arduino IDE**.
2. Add ESP32 board support: Go to **File → Preferences**, and under **Additional Boards Manager URLs**, add:
   ```
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```
3. Open **Tools → Board → Boards Manager**, search for `esp32` and install the official package.
4. Open **Tools → Manage Libraries...**, search for `ESP32Servo` and install it.
5. Open the firmware sketch located at:
   ```
   backend/firmware/recycling_arm_esp32/recycling_arm_esp32.ino
   ```
6. In **Tools → Board**, select `ESP32 Dev Module`.
7. Under **Tools → Port**, choose the COM port matching your plugged-in ESP32 (e.g. `COM4`, `COM7`).
8. Click **Upload** (arrow icon).
9. **Important:** Close the Arduino IDE Serial Monitor before attempting to connect the FastAPI backend. Windows permits only one application to hold an open serial handle at a time.

---

## 🚀 How to Start and Run the Application

Always start the **backend service first**, followed by the **frontend service**. Both need to run simultaneously in separate terminals.

### Terminal 1: Backend Service
```powershell
cd d:\Robotic_Arm\Robotic_interface\backend
.\.venv\Scripts\Activate.ps1
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
Expected output:
```text
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### Terminal 2: Frontend Service
```powershell
cd d:\Robotic_Arm\Robotic_interface\frontend
npm run dev
```
Expected output:
```text
   ▲ Next.js 15.1.0
   - Local:        http://localhost:3000
   - Network:      http://<your-ip>:3000

 ✓ Ready in 1.2s
```

---

## 🖥️ Using the Dashboard

1. **Access the Console:** Open your browser and navigate to **[http://localhost:3000](http://localhost:3000)**.
2. **System Health Status:**
   - Look at the top-right header: **BACKEND** will show green `Connected`.
   - **ESP32** chip will indicate `Connected` or `Disconnected` based on USB serial presence.
3. **Live Camera & Vision Stream:**
   - Scroll to **01 / VISION SYSTEM** (Camera Panel).
   - Click the **Start Camera** button.
   - The backend will initialize the OpenCV DirectShow webcam device, load the `yolo26n.pt` model, and stream real-time annotated JPEG frames into the viewport over WebSocket.
   - Click **Stop Camera** to shut down the video capture and free the webcam device.
4. **Bottle Detection Panel:**
   - Position a bottle in front of the camera.
   - The YOLO detector will draw a bounding box around the bottle in the video feed.
   - The **DETECTION CONFIDENCE** gauge updates in real time (e.g., `87.4%`).
   - The **Machine Vision** panel shows `BOTTLE DETECTED` with the confidence score.
5. **Hardware Serial Diagnostics:**
   - Open **[http://localhost:8000/docs](http://localhost:8000/docs)** to test the ESP32 connection.
   - Call `POST /api/esp32/connect` with your COM port.
   - Call `POST /api/esp32/test` to run a `PING` / `PONG` handshake with the microcontroller.

---

## 📡 Communication & Hardware Protocols

### WebSocket Protocol (`/ws`)

Clients connect to `ws://localhost:8000/ws`. The WebSocket serves two stream channels multiplexed over one connection:

#### 1. JSON Telemetry Updates (Text frames)
Broadcast periodically every 2 seconds and whenever system states change:
```json
{
  "type": "status",
  "data": {
    "backend": {
      "available": true,
      "message": "API is running"
    },
    "esp32": {
      "connected": true,
      "port": "COM7",
      "baud_rate": 115200,
      "available_ports": [
        { "device": "COM7", "description": "Silicon Labs CP210x USB to UART Bridge", "hwid": "..." }
      ],
      "message": "Serial port is open"
    },
    "camera": {
      "active": true,
      "device_index": 0,
      "message": "Camera is active"
    },
    "detection": {
      "running": true,
      "state": "bottle_detected",
      "detected": true,
      "detections": [
        {
          "label": "bottle",
          "confidence": 0.884,
          "box": { "x1": 180, "y1": 110, "x2": 420, "y2": 580 }
        }
      ],
      "confidence": 0.884,
      "classification": {
        "state": "uncertain",
        "confidence": null,
        "message": "Fill state is not inferred."
      },
      "model": "yolo26n.pt",
      "message": "Bottle detected with 88.4% confidence.",
      "updated_at": "2026-11-12T09:58:32.124Z"
    }
  }
}
```

#### 2. Annotated Video Feed (Binary frames)
While the camera is active, raw JPEG image bytes are streamed continuously as binary messages. The frontend converts these into `Blob` URLs for 30 FPS browser rendering.

---

### ESP32 Serial Protocol

The backend and ESP32 exchange **newline-delimited JSON** objects at **115200 baud**:

#### Ping Request & Response
- **Backend sends:**
  ```json
  {"command":"PING"}
  ```
- **ESP32 responds:**
  ```json
  {"status":"success","response":"PONG","device":"ESP32-Recycling-Arm"}
  ```

#### Status Request & Response
- **Backend sends:**
  ```json
  {"command":"GET_STATUS"}
  ```
- **ESP32 responds:**
  ```json
  {"status":"success","device":"ESP32-Recycling-Arm","firmware_version":"1.0.0","uptime_ms":45200}
  ```

---

## 📖 API Reference

Interactive Swagger documentation is available at `http://localhost:8000/docs`.

| Method | Endpoint | Description | Request Body Example |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/status` | Snapshot of all subsystems (backend, ESP32, camera, detection) | *None* |
| `GET` | `/api/esp32/status` | Check ESP32 serial link state & enumerate available COM ports | *None* |
| `POST` | `/api/esp32/connect` | Connect to an ESP32 COM port | `{"port": "COM7"}` *(or uses `.env`)* |
| `POST` | `/api/esp32/disconnect` | Close and release the serial COM port | *None* |
| `POST` | `/api/esp32/test` | Execute a `PING` command and verify `PONG` reply | *None* |
| `GET` | `/api/esp32/device-status` | Send `GET_STATUS` to ESP32 over serial | *None* |
| `GET` | `/api/camera/status` | Read camera capture status and device index | *None* |
| `POST` | `/api/camera/start` | Open webcam and start real-time YOLO detection | `{"device_index": 0}` *(optional)* |
| `POST` | `/api/camera/stop` | Release webcam hardware and stop detection | *None* |
| `GET` | `/api/detection/status` | Read current bottle detection results & confidence | *None* |
| `WS` | `/ws` | WebSocket endpoint for real-time telemetry and binary frames | *WebSocket connection* |

---

## ⚙️ Environment Variables

### Backend Configuration (`backend/.env`)

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `SERIAL_PORT` | string | `COM3` | The target COM port for ESP32 (e.g., `COM3`, `COM7`, `/dev/ttyUSB0`) |
| `BAUD_RATE` | int | `115200` | Serial baud rate (must match firmware configuration) |
| `SERIAL_TIMEOUT` | float | `2.0` | Serial read/write timeout in seconds |
| `CAMERA_INDEX` | int | `0` | OpenCV webcam index (`0` for primary/internal webcam, `1` for USB) |
| `YOLO_MODEL` | string | `yolo26n.pt` | Path or name of the YOLO weights file |
| `DETECTION_CONFIDENCE` | float | `0.25` | Minimum confidence score to register a bottle detection (0.01 - 0.99) |
| `DETECTION_IMAGE_SIZE` | int | `640` | Inference square dimension in pixels (e.g., 320, 640) |
| `CORS_ORIGINS` | string | `http://localhost:3000...` | Comma-separated list of allowed HTTP origins |
| `LOG_LEVEL` | string | `INFO` | Python log verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

### Frontend Configuration (`frontend/.env.local`)

| Variable | Default | Description |
| :--- | :--- | :--- |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Base HTTP endpoint of the FastAPI backend |
| `NEXT_PUBLIC_WS_URL` | `ws://localhost:8000` | Base WebSocket endpoint of the FastAPI backend |

---

## 🩺 Troubleshooting & Common Issues

### 1. PowerShell Script Execution Policy Error
**Symptom:** Running `.\.venv\Scripts\Activate.ps1` produces:
```text
File ... cannot be loaded because running scripts is disabled on this system.
```
**Resolution:** Run this command in your PowerShell session before activating:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### 2. COM Port Access Denied (`serial.serialutil.SerialException`)
**Symptom:** `Could not open COMx. Check the COM port and USB connection.`
**Resolution:**
- Verify if **Arduino IDE Serial Monitor** or another serial terminal (PuTTY, Tera Term) is open. Close it immediately.
- Open Windows **Device Manager → Ports (COM & LPT)** to verify your ESP32's assigned port number.
- Update `SERIAL_PORT` in `backend/.env` with the verified port.

### 3. Camera Fails to Open (`HardwareUnavailable: Could not open camera device 0`)
**Symptom:** Clicking "Start Camera" returns an error in the dashboard.
**Resolution:**
- Check if another application (Teams, Zoom, Discord, Windows Camera App) is currently using the camera.
- Try setting `CAMERA_INDEX=1` in `backend/.env` if you have both an integrated and an external webcam.
- On Windows, ensure camera privacy settings allow desktop applications to access your webcam.

### 4. Port 8000 or 3000 Already in Use
**Symptom:** `Error: listen EADDRINUSE: address already in use :::3000` or `Errno 10048`
**Resolution:**
Find and terminate the process occupying the port:
```powershell
# Check what is using port 8000
netstat -ano | findstr :8000
# Kill process by PID (e.g. PID 12345)
taskkill /F /PID 12345
```

### 5. WebSocket Connection Refused
**Symptom:** The dashboard shows `BACKEND: Disconnected` and camera controls are disabled.
**Resolution:**
- Ensure Uvicorn is running in Terminal 1 on `http://localhost:8000`.
- Verify `CORS_ORIGINS` in `backend/.env` includes `http://localhost:3000`.
- Verify `NEXT_PUBLIC_API_URL` and `NEXT_PUBLIC_WS_URL` in `frontend/.env.local` point to port `8000`.

---

## 📦 Production Deployment

To run the project in production mode:

### 1. Build and Run the Frontend
```powershell
cd d:\Robotic_Arm\Robotic_interface\frontend
npm run build
npm run start
```

### 2. Run the Backend Without Reload
```powershell
cd d:\Robotic_Arm\Robotic_interface\backend
.\.venv\Scripts\Activate.ps1
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1
```
*(Keep workers at 1 so that hardware handles to the webcam and COM port remain strictly single-threaded).*

---

## 📄 License & Credits

- **Project:** Circular Robotics Interface
- **Frameworks:** [FastAPI](https://fastapi.tiangolo.com/), [Next.js](https://nextjs.org/), [Ultralytics YOLO](https://github.com/ultralytics/ultralytics), [OpenCV](https://opencv.org/)
- **License:** MIT
