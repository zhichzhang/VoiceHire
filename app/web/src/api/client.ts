// app/web/src/api/client.ts

import {ENV} from "../config/env.ts";

const API_BASE_URL = ENV.API_BASE_URL;

export async function request<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });

  if (!res.ok) {
    let message = `Request failed with status ${res.status}`;

    try {
      const body = (await res.json()) as { detail?: unknown; message?: unknown };
      if (typeof body.detail === "string") message = body.detail;
      if (typeof body.message === "string") message = body.message;
    } catch {
      // ignore parse errors
    }

    throw new Error(message);
  }

  if (res.status === 204) {
    return undefined as T;
  }

  return (await res.json()) as T;
}