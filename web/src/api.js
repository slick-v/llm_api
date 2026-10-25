// Talks to the FastAPI backend. "/api" is proxied to the backend by Vite in
// dev and by nginx in Docker, so the browser only ever calls its own origin.
const API_BASE = "/api";

export const MAX_INPUT_CHARS = 2000;
const HISTORY_TO_SEND = 10; // the backend only uses the last 10 anyway
const USER_ID_KEY = "llm-chat-user-id";

/** An error whose message is safe to show to the user. */
export class BackendError extends Error {}

function randomId() {
  // crypto.randomUUID only exists on HTTPS or localhost
  if (window.crypto?.randomUUID) return window.crypto.randomUUID();
  return Date.now().toString(36) + Math.random().toString(36).slice(2);
}

// one id per browser, kept across refreshes, used for the per-user rate limit;
// after login this becomes the user's email
function getUserId() {
  try {
    let id = localStorage.getItem(USER_ID_KEY);
    if (!id) {
      id = randomId();
      localStorage.setItem(USER_ID_KEY, id);
    }
    return id;
  } catch {
    return "anonymous";
  }
}

async function errorMessage(response) {
  if (response.status === 422) {
    return "That message is too long or empty. Please shorten it and try again.";
  }
  try {
    // 429 and 502 come with a friendly "detail" from our backend
    const body = await response.json();
    if (typeof body.detail === "string") return body.detail;
  } catch {
    // not JSON, fall through
  }
  return "Something went wrong. Please try again.";
}

/**
 * Stream a reply from the backend, calling onChunk with each piece of text.
 * Throws BackendError for errors the user should see; when the request is
 * stopped through `signal`, throws whatever the abort was given.
 */
export async function streamChat({ messages, mode, signal, onChunk }) {
  let response;
  try {
    response = await fetch(`${API_BASE}/chat/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-User-Id": getUserId() },
      body: JSON.stringify({ messages: messages.slice(-HISTORY_TO_SEND), mode }),
      signal,
    });
  } catch (err) {
    if (signal?.aborted) throw err;
    throw new BackendError("Can't reach the server right now. Please try again.");
  }

  if (!response.ok) throw new BackendError(await errorMessage(response));

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
