import { useState } from "react";
import { loginUser } from "./api/auth.js";
import LoginForm from "./components/LoginForm.jsx";
import Dashboard from "./components/Dashboard.jsx";

export default function App() {
  const [user, setUser] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function login(username, password) {
    setBusy(true);
    setError("");
    try {
      const data = await loginUser(username, password);
      setUser(data.user);
    } catch (error) {
      setError(error.message);
    } finally {
      setBusy(false);
    }
  }

  function logout() {
    setUser(null);
    setError("");
  }

  function clearError() {
    setError("");
  }

  function handleError(error) {
    setError(error.message);
  }

  if (user === null) {
    return (
      <main className="login-shell">
        <LoginForm title="감시 서비스 로그인" onLogin={login} busy={busy} />
        {error && <p className="error" role="alert">{error}</p>}
      </main>
    );
  }
  return (
    <main className="shell">
      <header className="page-header">
        <div><h1>감시 서비스</h1><p>{user.username}님이 로그인했습니다.</p></div>
        <button onClick={logout} disabled={busy}>로그아웃</button>
      </header>
      {error && <p className="error" role="alert">{error}</p>}
      <Dashboard onError={handleError} onClearError={clearError} />
    </main>
  );
}
