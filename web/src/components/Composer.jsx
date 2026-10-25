import { useEffect, useRef } from "react";

import { MAX_INPUT_CHARS } from "../api.js";
import { SendIcon, StopIcon } from "./Icons.jsx";

// on phones Enter should add a new line; the send button sends
const isTouch = typeof window !== "undefined" && window.matchMedia("(pointer: coarse)").matches;

export default function Composer({ value, onChange, onSend, onStop, isStreaming }) {
  const textareaRef = useRef(null);

  // grow the box with its content, up to a limit
  useEffect(() => {
    const el = textareaRef.current;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
  }, [value]);

  function onKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey && !isTouch && !e.nativeEvent.isComposing) {
      e.preventDefault();
      onSend();
    }
  }

  const charsLeft = MAX_INPUT_CHARS - value.length;

  return (
    <form
      className="composer"
      onSubmit={(e) => {
        e.preventDefault();
        onSend();
      }}
    >
      <div className="composer-box">
        <textarea
          ref={textareaRef}
          rows={1}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Type your message…"
          maxLength={MAX_INPUT_CHARS}
          aria-label="Message"
        />
        {isStreaming ? (
          <button type="button" className="send-btn stop" onClick={onStop} aria-label="Stop generating">
            <StopIcon />
          </button>
        ) : (
          <button type="submit" className="send-btn" disabled={!value.trim()} aria-label="Send message">
            <SendIcon />
          </button>
        )}
      </div>
      <div className="composer-hint">
        <span className="muted keys-hint">{isTouch ? "" : "Enter to send · Shift+Enter for a new line"}</span>
        {charsLeft < 200 && (
          <span className={charsLeft <= 0 ? "warn" : "muted"}>{charsLeft} characters left</span>
        )}
      </div>
    </form>
  );
}
