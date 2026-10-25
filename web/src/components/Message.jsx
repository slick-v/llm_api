import { useState } from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { CheckIcon, CopyIcon } from "./Icons.jsx";

// links in replies open in a new tab
const markdownComponents = {
  a: (props) => <a {...props} target="_blank" rel="noopener noreferrer" />,
};

// the clipboard API only exists on HTTPS or localhost
const canCopy = typeof navigator !== "undefined" && !!navigator.clipboard;

function TypingDots() {
  return (
    <span className="typing" aria-label="Assistant is typing">
      <span />
      <span />
      <span />
    </span>
  );
}

export default function Message({ role, content, streaming }) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // copying is a convenience, ignore failures
    }
  }

  if (role === "user") {
    return (
      <div className="msg user">
        <div className="bubble">
          <p className="plain">{content}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="msg assistant">
      <div className="avatar" aria-hidden="true">🤖</div>
      <div className="bubble">
        {content ? (
          <div className="markdown">
            <Markdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
              {content}
            </Markdown>
          </div>
        ) : (
          <TypingDots />
        )}
        {canCopy && content && !streaming && (
          <div className="msg-actions">
            <button className="copy-btn" onClick={copy} aria-label="Copy reply">
              {copied ? <CheckIcon /> : <CopyIcon />}
              {copied ? "Copied" : "Copy"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
