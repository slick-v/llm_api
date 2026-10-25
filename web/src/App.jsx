import { useEffect, useState } from "react";

import { AuthError, clearToken, fetchMe, getToken, saveToken } from "./api.js";
import ChatPage, { chatStorageKey } from "./ChatPage.jsx";
import AuthScreen from "./components/AuthScreen.jsx";

function Background() {
  return (
    <div className="bg" aria-hidden="true">
      <span className="blob b1" />
      <span className="blob b2" />
      <span className="blob b3" />
    </div>
  );
}

export default function App() {
  // undefined = checking a saved token, null = logged out, object = logged in
  const [user, setUser] = useState(() => (getToken() ? undefined : null));
  const [notice, setNotice] = useState("");

  // a token from an earlier visit: ask the backend if it's still valid
  useEffect(() => {
    if (user !== undefined) return;
    fetchMe()
      .then(setUser)
      .catch((err) => {
        if (err instanceof AuthError) {
          clearToken();
          setNotice("Your session has expired. Please log in again.");
        } else {
          setNotice(err.message);
        }
        setUser(null);
      });
  }, [user]);

  function handleAuthenticated({ access_token, user: loggedIn }) {
    saveToken(access_token);
    setNotice("");
    setUser(loggedIn);
  }

  function logout(message = "") {
    if (user) {
      try {
        localStorage.removeItem(chatStorageKey(user.id)); // don't leave chats on a shared device
      } catch {
        // nothing to remove
      }
    }
    clearToken();
    setNotice(message);
    setUser(null);
  }

  return (
    <>
      <Background />
      {user === undefined && <div className="app-loading">Loading…</div>}
      {user === null && <AuthScreen onAuthenticated={handleAuthenticated} notice={notice} />}
      {user && <ChatPage user={user} onLogout={logout} />}
    </>
  );
}
