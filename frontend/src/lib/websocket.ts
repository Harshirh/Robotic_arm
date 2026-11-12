const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000";

/** Creates a socket only when explicitly called by a future integration. */
export function createWebSocket(path: string): WebSocket {
  return new WebSocket(new URL(path, WS_BASE_URL));
}
