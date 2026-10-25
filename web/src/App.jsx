import { useEffect, useRef, useState } from "react";

import { BackendError, checkHealth, streamChat } from "./api.js";
import Composer from "./components/Composer.jsx";
import { AlertIcon, CloseIcon, MenuIcon } from "./components/Icons.jsx";
import MessageList from "./components/MessageList.jsx";
import Sidebar from "./components/Sidebar.jsx";
import { DEFAULT_MODE, MODES } from "./modes.js";

const STORAGE_KEY = "llm-chat-state";
const CUT_OFF_NOTE = "\n\n_[The reply was cut off. Please try again.]_";
const CLEARED = "cleared";

// the chat is saved in this browser so a refresh doesn't lose it
function loadState() {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY));
    // drop anything the backend would reject: empty messages, and a user
    // message left without a reply (the page was closed mid-answer)
    const messages = (saved?.messages ?? []).filter((m) => m?.content);
    if (messages.at(-1)?.role === "user") messages.pop();
    const mode = MODES[saved?.mode] ? saved.mode : DEFAULT_MODE;
    return { messages, mode };
  } catch {
    return { messages: [], mode: DEFAULT_MODE };
  }
}

export default function App() {
  const [initial] = useState(loadState);
  const [messages, setMessages] = useState(initial.messages);
  const [mode, setMode] = useState(initial.mode);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [online, setOnline] = useState(null);
  const abortRef = useRef(null);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ messages, mode }));
    } catch {
      // private mode or storage full: the chat just won't survive a refresh
    }
  }, [messages, mode]);

  useEffect(() => {
    let active = true;
    const ping = () => checkHealth().then((ok) => active && setOnline(ok));
    ping();
    const timer = setInterval(ping, 30_000);
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, []);

  async function send(text) {
    const content = text.trim();
    if (!content || isStreaming) return;

    const before = messages;
    const history = [...messages, { role: "user", content }];
    setMessages([...history, { role: "assistant", content: "" }]);
    setInput("");
    setError("");
    setIsStreaming(true);

    const controller = new AbortController();
    abortRef.current = controller;
    let received = "";

    // nothing came back: undo the turn and give the text back to resend
    const undo = (message) => {
      setMessages(before);
      setInput(content);
      if (message) setError(message);
    };

    try {
      await streamChat({
        messages: history,
        mode,
        signal: controller.signal,
        onChunk: (chunk) => {
          received += chunk;
          setMessages([...history, { role: "assistant", content: received }]);
        },
      });
      if (!received) undo("The AI sent back an empty reply. Please try again.");
    } catch (err) {
      // "Clear chat" already emptied the conversation, leave it that way
      if (controller.signal.reason === CLEARED) return;
      const stopped = controller.signal.aborted;
      if (!received) {
        undo(stopped ? "" : err instanceof BackendError ? err.message : "Something went wrong. Please try again.");
      } else if (!stopped) {
        // keep the partial answer so the conversation still alternates user/assistant
        setMessages([...history, { role: "assistant", content: received + CUT_OFF_NOTE }]);
      }
    } finally {
      setIsStreaming(false);
      abortRef.current = null;
    }
  }

  function stop(reason = "stopped") {
    abortRef.current?.abort(reason);
  }

  function clearChat() {
    stop(CLEARED);
    setMessages([]);
    setError("");
    setSidebarOpen(false);
  }

  function changeMode(next) {
    setMode(next);
    setSidebarOpen(false);
  }

  const current = MODES[mode];

  return (
    <div className="app">
      <div className="bg" aria-hidden="true">
        <span className="blob b1" />
        <span className="blob b2" />
        <span className="blob b3" />
      </div>

      <Sidebar
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        mode={mode}
        onModeChange={changeMode}
        messageCount={messages.length}
        onClear={clearChat}
        online={online}
      />

      <main className="chat glass">
        <header className="chat-header">
          <button className="icon-btn menu-btn" onClick={() => setSidebarOpen(true)} aria-label="Open menu">
            <MenuIcon />
          </button>
          <span className="header-icon" aria-hidden="true">{current.icon}</span>
          <div>
            <h1>{current.label}</h1>
            <p className="muted">{current.description}</p>
          </div>
        </header>

        <MessageList messages={messages} isStreaming={isStreaming} mode={mode} onSuggestion={send} />

        {error && (
          <div className="error-banner" role="alert">
            <AlertIcon />
            <span>{error}</span>
            <button className="banner-close" onClick={() => setError("")} aria-label="Dismiss error">
              <CloseIcon />
            </button>
          </div>
        )}

        <Composer
          value={input}
          onChange={setInput}
          onSend={() => send(input)}
          onStop={() => stop()}
          isStreaming={isStreaming}
        />
      </main>
    </div>
  );
}
