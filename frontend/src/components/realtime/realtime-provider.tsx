"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { apiRequest } from "@/lib/api";
import { createWebSocket } from "@/lib/websocket";
import type { DetectionStatus } from "@/types";

type RealtimeContextValue = {
  backendConnected: boolean;
  esp32Connected: boolean | null;
  cameraActive: boolean | null;
  detection: DetectionStatus | null;
  frameUrl: string | null;
  cameraBusy: boolean;
  cameraError: string | null;
  startCamera: () => Promise<void>;
  stopCamera: () => Promise<void>;
};

const RealtimeContext = createContext<RealtimeContextValue | null>(null);

type StatusMessage = {
  type?: string;
  data?: { camera?: { active?: boolean }; detection?: DetectionStatus; esp32?: { connected?: boolean } };
};

export function RealtimeProvider({ children }: { children: React.ReactNode }) {
  const [backendConnected, setBackendConnected] = useState(false);
  const [esp32Connected, setEsp32Connected] = useState<boolean | null>(null);
  const [cameraActive, setCameraActive] = useState<boolean | null>(null);
  const [detection, setDetection] = useState<DetectionStatus | null>(null);
  const [frameUrl, setFrameUrl] = useState<string | null>(null);
  const [cameraBusy, setCameraBusy] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const currentFrameUrl = useRef<string | null>(null);

  useEffect(() => {
    let disposed = false;
    let socket: WebSocket | null = null;
    let retryTimer: number | undefined;

    const connect = () => {
      if (disposed) return;
      socket = createWebSocket("/ws");
      socket.onopen = () => setBackendConnected(true);
      socket.onmessage = async (event: MessageEvent<string | Blob | ArrayBuffer>) => {
        if (typeof event.data === "string") {
          try {
            const message = JSON.parse(event.data) as StatusMessage;
            if (message.type === "status" && message.data) {
              setCameraActive(message.data.camera?.active ?? false);
              setEsp32Connected(message.data.esp32?.connected ?? false);
              setDetection(message.data.detection ?? null);
              if (!message.data.camera?.active && currentFrameUrl.current) {
                URL.revokeObjectURL(currentFrameUrl.current);
                currentFrameUrl.current = null;
                setFrameUrl(null);
              }
            }
          } catch {
            // Ignore malformed status messages and keep the stream connection alive.
          }
          return;
        }

        const blob = event.data instanceof Blob ? event.data : new Blob([event.data], { type: "image/jpeg" });
        const nextUrl = URL.createObjectURL(blob);
        if (disposed) {
          URL.revokeObjectURL(nextUrl);
          return;
        }
        if (currentFrameUrl.current) URL.revokeObjectURL(currentFrameUrl.current);
        currentFrameUrl.current = nextUrl;
        setFrameUrl(nextUrl);
      };
      socket.onclose = () => {
        setBackendConnected(false);
        setCameraActive(null);
        setEsp32Connected(null);
        if (currentFrameUrl.current) URL.revokeObjectURL(currentFrameUrl.current);
        currentFrameUrl.current = null;
        setFrameUrl(null);
        if (!disposed) retryTimer = window.setTimeout(connect, 2000);
      };
      socket.onerror = () => socket?.close();
    };

    connect();
    return () => {
      disposed = true;
      if (retryTimer !== undefined) window.clearTimeout(retryTimer);
      socket?.close();
      if (currentFrameUrl.current) URL.revokeObjectURL(currentFrameUrl.current);
      currentFrameUrl.current = null;
    };
  }, []);

  const cameraAction = useCallback(async (action: "start" | "stop") => {
    setCameraBusy(true);
    setCameraError(null);
    try {
      const result = await apiRequest<{ active: boolean; detection?: DetectionStatus }>(`/api/camera/${action}`, { method: "POST" });
      setCameraActive(result.active);
      if (result.detection) setDetection(result.detection);
      if (!result.active && currentFrameUrl.current) {
        URL.revokeObjectURL(currentFrameUrl.current);
        currentFrameUrl.current = null;
        setFrameUrl(null);
      }
    } catch (error) {
      const apiError = error as { message?: string };
      setCameraError(apiError.message ?? "Camera request failed. Check the backend connection.");
    } finally {
      setCameraBusy(false);
    }
  }, []);

  const value = useMemo<RealtimeContextValue>(() => ({
    backendConnected,
    esp32Connected,
    cameraActive,
    detection,
    frameUrl,
    cameraBusy,
    cameraError,
    startCamera: () => cameraAction("start"),
    stopCamera: () => cameraAction("stop"),
  }), [backendConnected, esp32Connected, cameraActive, detection, frameUrl, cameraBusy, cameraError, cameraAction]);

  return <RealtimeContext.Provider value={value}>{children}</RealtimeContext.Provider>;
}

export function useRealtime() {
  const value = useContext(RealtimeContext);
  if (!value) throw new Error("useRealtime must be used within RealtimeProvider");
  return value;
}
