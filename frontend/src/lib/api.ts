import type { ApiError } from "@/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/** Typed fetch wrapper for future FastAPI endpoints. No requests are made until called. */
export async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(new URL(path, API_BASE_URL), {
      ...init,
      headers: { "Content-Type": "application/json", ...init?.headers },
    });
  } catch {
    throw { message: "Could not reach the API. Check that the backend is running." } satisfies ApiError;
  }
  if (!response.ok) {
    throw { message: `API request failed (${response.status})`, status: response.status } satisfies ApiError;
  }
  return response.json() as Promise<T>;
}
