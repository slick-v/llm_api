// Talks to the FastAPI backend. "/api" is proxied to the backend by Vite in
// dev and by nginx in Docker, so the browser only ever calls its own origin.
const API_BASE = "/api";

export const MAX_INPUT_CHARS = 2000;
const HISTORY_TO_SEND = 10; // the backend only uses the last 10 anyway
const TOKEN_KEY = "llm-chat-token";

/** An error whose message is safe to show to the user. */
export class BackendError extends Error {}

/** No token, or it expired / is invalid: the user has to log in again. */
export class AuthError extends BackendError {}

export function getToken() {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function saveToken(token) {
  try {
    localStorage.setItem(TOKEN_KEY, token);
  } catch {
    // storage blocked: the user will just have to log in after a refresh
  }
}

export function clearToken() {
  try {
    localStorage.removeItem(TOKEN_KEY);
  } catch {
    // nothing to clear
  }
}

async function errorMessage(response, invalidMessage) {
  if (response.status === 422) return invalidMessage;
  try {
    // our backend sends a friendly "detail" for 401, 409, 429 and 502
    const body = await response.json();
    if (typeof body.detail === "string") return body.detail;
  } catch {
    // not JSON, fall through
  }
  return "Something went wrong. Please try again.";
}

// fetch wrapper: adds the token, turns failures into BackendError / AuthError
async function request(
  path,
  { method = "GET", body, signal, invalidMessage } = {},
) {
  const token = getToken();
  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      method,
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: body === undefined ? undefined : JSON.stringify(body),
      signal,
    });
  } catch (err) {
    if (signal?.aborted) throw err;
    throw new BackendError(
      "Can't reach the server right now. Please try again.",
    );
  }

  const fallback =
    invalidMessage ?? "Please check what you entered and try again.";
  if (response.status === 401)
    throw new AuthError(await errorMessage(response, fallback));
  if (!response.ok)
    throw new BackendError(await errorMessage(response, fallback));
  return response;
}

const AUTH_INVALID =
  "Enter a valid email and a password of at least 8 characters.";

/** Returns { access_token, user } */
export async function register(email, password) {
  const response = await request("/auth/register", {
    method: "POST",
    body: { email, password },
    invalidMessage: AUTH_INVALID,
  });
  return response.json();
}

/** Returns { access_token, user } */
export async function login(email, password) {
  const response = await request("/auth/login", {
    method: "POST",
    body: { email, password },
    invalidMessage: AUTH_INVALID,
  });
  return response.json();
}

export async function fetchMe() {
  const response = await request("/auth/me");
  return response.json();
}

/**
 * Stream a reply from the backend, calling onChunk with each piece of text.
 * Throws AuthError when the login has expired, BackendError for other errors
 * the user should see; when stopped through `signal`, throws the abort reason.
 */
export async function streamChat({ messages, mode, signal, onChunk }) {
  const response = await request("/chat/stream", {
    method: "POST",
    body: { messages: messages.slice(-HISTORY_TO_SEND), mode },
    signal,
    invalidMessage:
      "That message is too long or empty. Please shorten it and try again.",
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    onChunk(decoder.decode(value, { stream: true }));
  }
}

export async function checkHealth() {
  try {
    const response = await fetch(`${API_BASE}/health`, { cache: "no-store" });
    return response.ok;
  } catch {
    return false;
  }
}
