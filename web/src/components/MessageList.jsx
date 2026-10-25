import { useEffect, useRef } from "react";

import { MODES } from "../modes.js";
import Message from "./Message.jsx";

function EmptyState({ mode, onSuggestion }) {
  const m = MODES[mode];
  return (
    <div className="empty">
      <div className="empty-icon">{m.icon}</div>
      <h2>How can I help?</h2>
      <p className="muted">{m.description}. Pick a starter or type your own message.</p>
      <div className="suggestions">
        {m.suggestions.map((s) => (
          <button key={s} className="chip" onClick={() => onSuggestion(s)}>
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}

export default function MessageList({ messages, isStreaming, mode, onSuggestion }) {
  const listRef = useRef(null);
  // follow new text only while the user is at the bottom, so scrolling up
  // to read an earlier message isn't interrupted by the stream
  const stickToBottom = useRef(true);

  function onScroll() {
    const el = listRef.current;
    stickToBottom.current = el.scrollHeight - el.scrollTop - el.clientHeight < 80;
  }

  // a new message (the user just sent one) always jumps to the bottom
  useEffect(() => {
    stickToBottom.current = true;
  }, [messages.length]);

  useEffect(() => {
    const el = listRef.current;
    if (el && stickToBottom.current) el.scrollTop = el.scrollHeight;
  }, [messages]);

  return (
    <div className="messages" ref={listRef} onScroll={onScroll} aria-live="polite">
      {messages.length === 0 ? (
        <EmptyState mode={mode} onSuggestion={onSuggestion} />
      ) : (
        messages.map((msg, i) => (
          <Message
            key={i}
            role={msg.role}
            content={msg.content}
            streaming={isStreaming && i === messages.length - 1}
          />
        ))
      )}
    </div>
  );
}
