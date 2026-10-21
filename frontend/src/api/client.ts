const TOKENS_KEY = "keyhouse.tokens";

interface Tokens {
  access: string;
  refresh: string;
}

export class ApiError extends Error {
  status: number;
  data: unknown;

  constructor(status: number, data: unknown) {
    super(errorMessage(data, status));
    this.status = status;
    this.data = data;
  }
}

// --- Token storage ---------------------------------------------------------
// Storage can be unavailable (private mode, blocked site data), so every access is guarded.

export function getTokens(): Tokens | null {
  try {
    const raw = localStorage.getItem(TOKENS_KEY);
    return raw ? (JSON.parse(raw) as Tokens) : null;
  } catch {
    return null;
  }
}

export function setTokens(tokens: Tokens | null) {
  try {
    if (tokens) localStorage.setItem(TOKENS_KEY, JSON.stringify(tokens));
    else localStorage.removeItem(TOKENS_KEY);
  } catch {
    // Without storage the session simply lasts until the tab closes.
  }
}

let onSessionExpired: () => void = () => {};
export function handleSessionExpired(callback: () => void) {
  onSessionExpired = callback;
}

// --- Requests ----------------------------------------------------------------

type Body = Record<string, unknown> | FormData;

interface RequestOptions {
  method?: "GET" | "POST" | "PATCH" | "DELETE";
  body?: Body;
  params?: Record<string, string | number | undefined | null>;
}

let refreshing: Promise<boolean> | null = null;

async function refreshAccessToken(): Promise<boolean> {
  const tokens = getTokens();
  if (!tokens) return false;
  // Several requests may fail at once; share a single refresh between them.
  refreshing ??= fetch("/api/auth/refresh/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh: tokens.refresh }),
  })
    .then(async (response) => {
      if (!response.ok) return false;
      const data = (await response.json()) as { access: string };
      setTokens({ ...tokens, access: data.access });
      return true;
    })
    .catch(() => false)
    .finally(() => {
      refreshing = null;
    });
  return refreshing;
}

function buildUrl(path: string, params?: RequestOptions["params"]) {
  const url = new URL(path, window.location.origin);
  for (const [key, value] of Object.entries(params ?? {})) {
    if (value !== undefined && value !== null && value !== "") url.searchParams.set(key, String(value));
  }
  return url.pathname + url.search;
}

export async function api<T>(path: string, options: RequestOptions = {}, retry = true): Promise<T> {
  const { method = "GET", body, params } = options;
  const headers: Record<string, string> = { Accept: "application/json" };
  const tokens = getTokens();
  if (tokens) headers.Authorization = `Bearer ${tokens.access}`;

  let payload: BodyInit | undefined;
  if (body instanceof FormData) {
    payload = body; // The browser sets the multipart boundary.
  } else if (body) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }

  let response: Response;
  try {
    response = await fetch(buildUrl(path, params), { method, headers, body: payload });
  } catch {
    throw new ApiError(0, { detail: "Can't reach the server. Check your connection and try again." });
  }

  if (response.status === 401 && tokens && retry) {
    if (await refreshAccessToken()) return api<T>(path, options, false);
    setTokens(null);
    onSessionExpired();
  }

  if (response.status === 204) return undefined as T;
  const data = await response.json().catch(() => null);
  if (!response.ok) throw new ApiError(response.status, data);
  return data as T;
}

// --- Error messages ------------------------------------------------------------

/** Turn a DRF error payload into one readable sentence. */
export function errorMessage(data: unknown, status = 0): string {
  if (data && typeof data === "object") {
    const record = data as Record<string, unknown>;
    if (typeof record.detail === "string") return record.detail;
    for (const value of Object.values(record)) {
      const first = Array.isArray(value) ? value[0] : value;
      if (typeof first === "string") return first;
      if (first && typeof first === "object") return errorMessage(first, status);
    }
  }
  if (status === 429) return "Too many attempts. Wait a minute, then try again.";
  if (status >= 500) return "The server ran into a problem. Try again in a moment.";
  return "Something went wrong. Try again.";
}

/** Field-level messages, for showing errors next to the matching input. */
export function fieldErrors(error: unknown): Record<string, string> {
  if (!(error instanceof ApiError) || !error.data || typeof error.data !== "object") return {};
  const out: Record<string, string> = {};
  for (const [key, value] of Object.entries(error.data as Record<string, unknown>)) {
    const first = Array.isArray(value) ? value[0] : value;
    if (typeof first === "string") out[key] = first;
  }
  return out;
}
