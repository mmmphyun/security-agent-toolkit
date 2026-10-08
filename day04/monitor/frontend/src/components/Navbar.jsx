import { Activity, RefreshCw, LogOut, User } from "lucide-react";

export default function Navbar({ username, onRefreshAll, onLogout, refreshing }) {
  return (
    <header className="w-full bg-surface border-b border-border px-6 py-3 sticky top-0 z-20">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded flex items-center justify-center bg-background border border-border text-accent">
            <Activity className="w-4 h-4" />
          </div>
          <div>
            <h1 className="text-base font-bold text-foreground leading-tight">
              Mini Watch 관제 콕핏
            </h1>
            <p className="text-xs text-muted">실시간 HTTP 이벤트 및 관찰 메모</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded bg-background border border-border text-xs text-foreground">
            <User className="w-3.5 h-3.5 text-accent" />
            <span className="font-medium">{username}</span>
            <span className="text-muted">(운영자)</span>
          </div>

          <button
            type="button"
            onClick={onRefreshAll}
            disabled={refreshing}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium bg-background border border-border text-foreground hover:bg-surface/80 disabled:opacity-50 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
            aria-label="데이터 새로고침"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin text-accent" : ""}`} />
            <span>새로고침</span>
          </button>

          <button
            type="button"
            onClick={onLogout}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium bg-red-950/40 border border-red-800/50 text-red-300 hover:bg-red-900/50 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-400"
            aria-label="로그아웃"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>로그아웃</span>
          </button>
        </div>
      </div>
    </header>
  );
}
