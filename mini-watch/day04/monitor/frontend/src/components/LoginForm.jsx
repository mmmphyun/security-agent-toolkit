import { useState } from "react";
import { ShieldCheck, LogIn, AlertCircle } from "lucide-react";
import { login } from "../api/auth";

export default function LoginForm({ onLoginSuccess }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (!username.trim() || !password.trim()) {
      setError("아이디와 비밀번호를 모두 입력해 주세요.");
      return;
    }

    setSubmitting(true);
    try {
      const result = await login(username.trim(), password.trim());
      if (result && result.user) {
        onLoginSuccess(result.user);
      }
    } catch (err) {
      setError(err.message || "로그인 요청에 실패했습니다.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="min-h-screen flex items-center justify-center p-4 bg-background">
      <div className="w-full max-w-md p-6 rounded-lg border border-border bg-surface shadow-elevation-3">
        <header className="mb-6 text-center">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-full mb-3 bg-background border border-border text-accent">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <h1 className="text-xl font-bold tracking-tight text-foreground">
            Mini Watch 관제 대시보드
          </h1>
          <p className="text-sm mt-1 text-muted">
            운영자 계정으로 로그인하여 시스템 요청 및 메모를 관리합니다.
          </p>
        </header>

        {error && (
          <div
            role="alert"
            className="mb-4 p-3 rounded flex items-center gap-2 text-sm bg-background border border-red-500/30 text-red-400"
          >
            <AlertCircle className="w-4 h-4 shrink-0 text-red-400" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4" role="form" aria-label="운영자 로그인 폼">
          <div>
            <label
              htmlFor="login-username"
              className="block text-xs font-medium mb-1 text-muted"
            >
              운영자 아이디
            </label>
            <input
              id="login-username"
              type="text"
              autoComplete="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="operator"
              disabled={submitting}
              className="w-full px-3 py-2 text-sm rounded bg-background border border-border text-foreground placeholder:text-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
            />
          </div>

          <div>
            <label
              htmlFor="login-password"
              className="block text-xs font-medium mb-1 text-muted"
            >
              비밀번호
            </label>
            <input
              id="login-password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              disabled={submitting}
              className="w-full px-3 py-2 text-sm rounded bg-background border border-border text-foreground placeholder:text-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
            />
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full mt-2 py-2 px-4 rounded text-sm font-semibold flex items-center justify-center gap-2 bg-accent text-slate-950 hover:opacity-90 disabled:opacity-50 transition-opacity focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
          >
            <LogIn className="w-4 h-4" />
            <span>{submitting ? "확인 중..." : "로그인"}</span>
          </button>
        </form>

        <footer className="mt-6 pt-4 border-t border-border text-center text-xs text-muted">
          기본 실습 계정: operator / Learn123!
        </footer>
      </div>
    </main>
  );
}
