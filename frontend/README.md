# Circular Robotics Control Center

Responsive Next.js dashboard starter for the recycling robotic arm project. It contains no hardware connections or movement commands. API and WebSocket helpers are only invoked when explicitly called from application code.

## Setup

```bash
cd frontend
npm install
Copy-Item .env.example .env.local
npm run dev
```

Open http://localhost:3000. Set `NEXT_PUBLIC_API_URL` and `NEXT_PUBLIC_WS_URL` in `.env.local` to the FastAPI service origin when it is available. The API helper is in `src/lib/api.ts`; the WebSocket factory is in `src/lib/websocket.ts`.

Production build and run:

```bash
npm run build
npm run start
```
