// app/web/src/api/env.ts

export const ENV = {
  API_BASE_URL:
    import.meta.env.VITE_API_BASE_URL,
} as const;

if (!ENV.API_BASE_URL) {
  throw new Error(
    "VITE_API_BASE_URL is missing",
  );
}