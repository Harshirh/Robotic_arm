# Recycling Robotic Arm API

FastAPI backend for status reporting, ESP32 serial communication, webcam streaming, and bottle-presence detection. Fill-state classification and servo movement are not implemented. Serial and camera connections are independent and are never opened automatically at startup.

## Windows setup (PowerShell)

```powershell
cd D:\Robotic_Arm\Robotic_interface\backend
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` to set `SERIAL_PORT` to the ESP32's Windows COM port (for example `COM4`) and `CAMERA_INDEX` if needed. Neither device is opened until its connect/start endpoint is called. The first camera start loads the `YOLO_MODEL` weights; if they are not cached locally, Ultralytics downloads them and requires internet access. For an offline setup, place the model weights locally and set `YOLO_MODEL` to that path. Start the API with:

```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Interactive API documentation is available at http://localhost:8000/docs. The configured CORS origins include the Next.js frontend at http://localhost:3000.

## ESP32 firmware

Open `firmware/recycling_arm_esp32.ino` in Arduino IDE, select your ESP32 DevKit board and its CP2102 COM port, install **ArduinoJson 6.x** from Library Manager, then upload. Close Arduino Serial Monitor before connecting from FastAPI because only one application can own the COM port at a time. Configure the same COM port in `.env` and leave the baud rate at `115200`.

The firmware accepts one JSON object per line. It responds to `PING` with a `PONG` response and device information, responds to `GET_STATUS` with current firmware/device status, and returns a JSON error for malformed or unsupported commands. It does not initialize or move servos.

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/status` | Combined backend, ESP32, camera, and detection status |
| GET | `/api/esp32/status` | Serial connection and available COM ports |
| POST | `/api/esp32/connect` | Open configured port; optionally send `{"port":"COM4"}` |
| POST | `/api/esp32/disconnect` | Close the serial connection |
| POST | `/api/esp32/test` | Send `{"command":"PING"}` and require a `PONG` response |
| GET | `/api/esp32/device-status` | Query device status over JSON serial protocol |
| GET | `/api/camera/status` | Camera state |
| POST | `/api/camera/start` | Open camera; optionally send `{"device_index":0}` |
| POST | `/api/camera/stop` | Release camera device |
| GET | `/api/detection/status` | Bottle-presence state, boxes, detector confidence, and separate fill-state result |
| WS | `/ws` | JSON status snapshots and binary annotated JPEG frames |

### Webcam detection

Call `POST /api/camera/start` to open the configured laptop webcam and begin inference; call `POST /api/camera/stop` to stop inference and release it. Bottle presence is detected with the pretrained Ultralytics YOLO model (`yolo26n.pt`) using its COCO `bottle` class. Boxes are drawn into JPEG frames, which are broadcast as WebSocket binary messages. JSON messages use `{"type":"status","data":{...}}` and include the camera and detection states. Frames are streamed only while a camera is active.

The YOLO score is object-detection confidence only. Fill-state is deliberately separate: a detected bottle reports classification as `uncertain`, with no fill-state confidence. Neither an empty nor a not-empty result is inferred from transparency. Camera read failure marks detection `camera_disconnected`, releases the camera, and stops the stream; call the camera start endpoint again to retry.

Hardware errors return a JSON `error` object with a stable `code`, human-readable `message`, and affected `resource`. An unavailable camera does not affect serial state, and an unavailable ESP32 does not affect camera state.
