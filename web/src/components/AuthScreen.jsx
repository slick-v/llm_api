import { useState } from "react";

import { BackendError, login, register } from "../api.js";

export default function AuthScreen({ onAuthenticated, notice }) {
  const [tab, setTab] = useState("login"); // "login" or "register"
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const isRegister = tab === "register";

  function switchTab(next) {
    setTab(next);
    setError("");
  }

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const result = isRegister ? await register(email, password) : await login(email, password);
      onAuthenticated(result); // this screen unmounts, so no setBusy(false) needed
    } catch (err) {
      setError(err instanceof BackendError ? err.message : "Something went wrong. Please try again.");
      setBusy(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card glass">
        <div className="brand auth-brand">
          <span className="brand-logo">💬</span>
          <span className="brand-name">LLM Chat</span>
        </div>

        <h1 className="auth-title">{isRegister ? "Create your account" : "Welcome back"}</h1>
        <p className="muted auth-subtitle">
          {isRegister ? "Sign up to start chatting." : "Log in to continue your chats."}
        </p>

        <div className="auth-tabs" role="tablist">
          <button
            type="button"
            role="tab"
            aria-selected={!isRegister}
            className={!isRegister ? "active" : ""}
            onClick={() => switchTab("login")}
          >
            Log in
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={isRegister}
            className={isRegister ? "active" : ""}
            onClick={() => switchTab("register")}
          >
            Sign up
          </button>
        </div>

        {notice && !error && <div className="info-banner">{notice}</div>}
        {error && (
          <div className="auth-error" role="alert">
            {error}
          </div>
        )}

        <form onSubmit={onSubmit} className="auth-form">
          <label className="field">
            <span>Email</span>
            <input
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
            />
          </label>

          <label className="field">
            <span>Password</span>
            <input
              type="password"
              autoComplete={isRegister ? "new-password" : "current-password"}
              required
              minLength={isRegister ? 8 : undefined}
              maxLength={128}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={isRegister ? "At least 8 characters" : "Your password"}
            />
          </label>

          <button type="submit" className="auth-submit" disabled={busy}>
            {busy ? "Please wait…" : isRegister ? "Create account" : "Log in"}
          </button>
        </form>
      </div>
    </div>
  );
}
