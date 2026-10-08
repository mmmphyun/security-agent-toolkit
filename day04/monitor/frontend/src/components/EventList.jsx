import { useState, useMemo } from "react";
import { Search, Filter, AlertCircle, RefreshCw, Database } from "lucide-react";

export default function EventList({
  events = [],
  loading = false,
  error = null,
  onRetry,
}) {
  const [pathFilter, setPathFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");

  const filteredEvents = useMemo(() => {
    return events.filter((ev) => {
      const matchPath = ev.path
        ? ev.path.toLowerCase().includes(pathFilter.trim().toLowerCase())
        : true;
      const matchStatus =
        statusFilter === "ALL"
          ? true
          : statusFilter === "ERROR"
          ? Number(ev.status_code) >= 400
          : statusFilter === "2XX"
          ? Number(ev.status_code) >= 200 && Number(ev.status_code) < 300
          : statusFilter === "3XX"
          ? Number(ev.status_code) >= 300 && Number(ev.status_code) < 400
          : statusFilter === "4XX"
          ? Number(ev.status_code) >= 400 && Number(ev.status_code) < 500
          : statusFilter === "5XX"
          ? Number(ev.status_code) >= 500
          : true;
      return matchPath && matchStatus;
    });
  }, [events, pathFilter, statusFilter]);

  const getStatusBadge = (statusCode) => {
    const code = Number(statusCode);
    if (code >= 200 && code < 300) {
      return (
        <span className="px-1.5 py-0.5 rounded text-[11px] font-semibold bg-emerald-950/60 text-emerald-400 border border-emerald-800/40">
          {code} OK
        </span>
      );
    }
    if (code >= 300 && code < 400) {
      return (
        <span className="px-1.5 py-0.5 rounded text-[11px] font-semibold bg-blue-950/60 text-blue-400 border border-blue-800/40">
          {code} REDIR
        </span>
      );
    }
    if (code >= 400 && code < 500) {
      return (
        <span className="px-1.5 py-0.5 rounded text-[11px] font-semibold bg-amber-950/60 text-amber-400 border border-amber-800/40">
          {code} CLIENT
        </span>
      );
    }
    return (
      <span className="px-1.5 py-0.5 rounded text-[11px] font-semibold bg-red-950/60 text-red-400 border border-red-800/40">
        {code} SERVER
      </span>
    );
  };

  const getMethodBadge = (method) => {
    const m = (method || "").toUpperCase();
    const colors = {
      GET: "bg-sky-950/60 text-sky-400 border-sky-800/40",
      POST: "bg-emerald-950/60 text-emerald-400 border-emerald-800/40",
      PUT: "bg-amber-950/60 text-amber-400 border-amber-800/40",
      DELETE: "bg-rose-950/60 text-rose-400 border-rose-800/40",
    };
    const cls = colors[m] || "bg-slate-800 text-slate-300 border-slate-700";
    return (
      <span className={`px-1.5 py-0.5 rounded font-mono text-[10px] font-bold border ${cls}`}>
        {m}
      </span>
    );
  };

  return (
    <section
      aria-label="일반 서비스 요청 기록"
      className="p-4 rounded-lg bg-surface border border-border flex flex-col h-full shadow-elevation-2"
    >
      <header className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-3 pb-3 border-b border-border">
        <div>
          <h2 className="text-sm font-bold text-foreground flex items-center gap-2">
            <Database className="w-4 h-4 text-accent" />
            <span>수집된 요청 기록</span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-background border border-border text-muted">
              {filteredEvents.length}건
            </span>
          </h2>
          <p className="text-[11px] text-muted mt-0.5">
            일반 서비스(포트 5100)에서 실시간으로 전달된 HTTP 접근 내역
          </p>
        </div>

        {/* 필터 툴바 */}
        <div className="flex items-center gap-2 w-full sm:w-auto">
          <div className="relative flex-1 sm:w-44">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-muted" />
            <input
              type="text"
              placeholder="경로 검색 (/posts...)"
              value={pathFilter}
              onChange={(e) => setPathFilter(e.target.value)}
              className="w-full pl-8 pr-2 py-1 text-xs rounded bg-background border border-border text-foreground placeholder:text-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
              aria-label="요청 경로 필터"
            />
          </div>

          <div className="relative">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="text-xs py-1 px-2 pr-6 rounded bg-background border border-border text-foreground appearance-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
              aria-label="상태 코드 필터"
            >
              <option value="ALL">전체 상태</option>
              <option value="2XX">2xx (정상)</option>
              <option value="3XX">3xx (리다이렉트)</option>
              <option value="4XX">4xx (클라이언트)</option>
              <option value="5XX">5xx (서버 오류)</option>
              <option value="ERROR">오류 전체 (≥400)</option>
            </select>
            <Filter className="w-3 h-3 absolute right-2 top-1/2 -translate-y-1/2 text-muted pointer-events-none" />
          </div>
        </div>
      </header>

      {/* 4-State 구현 */}
      {/* 1. Loading State */}
      {loading && (
        <div aria-busy="true" className="flex-1 flex flex-col justify-center items-center py-12 text-muted gap-2">
          <RefreshCw className="w-5 h-5 animate-spin text-accent" />
          <span className="text-xs">요청 기록을 조회하는 중입니다...</span>
        </div>
      )}

      {/* 2. Error State */}
      {!loading && error && (
        <div role="alert" className="flex-1 flex flex-col justify-center items-center py-10 px-4 text-center">
          <AlertCircle className="w-6 h-6 text-red-400 mb-2" />
          <p className="text-xs font-medium text-red-300 mb-2">{error}</p>
          {onRetry && (
            <button
              type="button"
              onClick={onRetry}
              className="px-3 py-1 text-xs rounded bg-background border border-border text-foreground hover:bg-surface focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
            >
              다시 시도
            </button>
          )}
        </div>
      )}

      {/* 3. Empty State */}
      {!loading && !error && filteredEvents.length === 0 && (
        <div className="flex-1 flex flex-col justify-center items-center py-12 text-center text-muted">
          <Database className="w-8 h-8 stroke-1 mb-2 opacity-50" />
          <p className="text-xs font-medium text-foreground">수집된 요청 기록이 없습니다.</p>
          <p className="text-[11px] text-muted mt-1 max-w-xs">
            일반 서비스(포트 5100)의 게시판을 이용하면 이곳에 요청 로그가 자동으로 수집됩니다.
          </p>
        </div>
      )}

      {/* 4. Populated State */}
      {!loading && !error && filteredEvents.length > 0 && (
        <div className="flex-1 overflow-x-auto overflow-y-auto max-h-[460px]">
          <table className="w-full text-left text-xs border-collapse" role="table">
            <thead className="sticky top-0 bg-surface/90 backdrop-blur border-b border-border text-muted">
              <tr>
                <th className="py-2 px-2.5 font-medium w-16">ID</th>
                <th className="py-2 px-2.5 font-medium w-20">메서드</th>
                <th className="py-2 px-2.5 font-medium">요청 경로</th>
                <th className="py-2 px-2.5 font-medium w-24">상태 코드</th>
                <th className="py-2 px-2.5 font-medium w-36 text-right">발생 시각</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/60">
              {filteredEvents.map((ev) => (
                <tr key={ev.id || `${ev.method}-${ev.path}-${ev.occurred_at}`} className="hover:bg-background/50 transition-colors">
                  <td className="py-2 px-2.5 font-mono text-muted text-[11px]">#{ev.id}</td>
                  <td className="py-2 px-2.5">{getMethodBadge(ev.method)}</td>
                  <td className="py-2 px-2.5 font-mono text-foreground break-all">{ev.path}</td>
                  <td className="py-2 px-2.5">{getStatusBadge(ev.status_code)}</td>
                  <td className="py-2 px-2.5 text-muted text-right text-[11px] whitespace-nowrap">
                    {ev.occurred_at ? new Date(ev.occurred_at).toLocaleTimeString() : "-"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
