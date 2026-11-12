export type ConnectionState = "connected" | "connecting" | "disconnected";

export interface SystemStatus {
  connection: ConnectionState;
  lastSeen?: string;
  message?: string;
}

export interface CameraFrame {
  imageUrl: string;
  capturedAt: string;
}

export type ApiError = { message: string; status?: number };

export type BottleDetectionState =
  | "waiting"
  | "bottle_detected"
  | "no_bottle_detected"
  | "unavailable"
  | "camera_disconnected";

export interface DetectionStatus {
  running: boolean;
  state: BottleDetectionState;
  detected: boolean | null;
  detections: Array<{
    label: string;
    confidence: number;
    box: { x1: number; y1: number; x2: number; y2: number };
  }>;
  confidence: number | null;
  classification: { state: string; confidence: number | null; message: string };
  model: string;
  message: string;
  updated_at: string | null;
}
