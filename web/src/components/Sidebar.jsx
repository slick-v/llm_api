import { MODES } from "../modes.js";
import { CloseIcon, TrashIcon } from "./Icons.jsx";

function statusText(online) {
  if (online === null) return "Checking server…";
  return online ? "Server online" : "Server offline";
}

export default function Sidebar({ open, onClose, mode, onModeChange, messageCount, onClear, online }) {
  return (
    <>
      <div className={`scrim ${open ? "show" : ""}`} onClick={onClose} aria-hidden="true" />
      <aside className={`sidebar glass ${open ? "open" : ""}`} aria-label="Chat settings">
        <div className="brand">
          <span className="brand-logo">💬</span>
          <span className="brand-name">LLM Chat</span>
          <button className="icon-btn close-btn" onClick={onClose} aria-label="Close menu">
            <CloseIcon />
          </button>
        </div>

        <p className="section-label">Mode</p>
        <nav className="modes">
          {Object.entries(MODES).map(([key, m]) => (
            <button
              key={key}
              className={`mode-card ${key === mode ? "active" : ""}`}
              onClick={() => onModeChange(key)}
              aria-pressed={key === mode}
            >
              <span className="mode-icon">{m.icon}</span>
              <span>
                <span className="mode-label">{m.label}</span>
                <span className="mode-desc">{m.description}</span>
              </span>
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="stat">
            <span className="muted">Messages</span>
            <strong>{messageCount}</strong>
          </div>
          <button className="ghost-btn" onClick={onClear} disabled={!messageCount}>
            <TrashIcon /> Clear chat
          </button>
          <div className="status">
            <span className={`dot ${online === null ? "" : online ? "ok" : "down"}`} />
            {statusText(online)}
          </div>
        </div>
      </aside>
    </>
  );
}
