import { Radio, CheckCircle2, AlertTriangle, FileText } from "lucide-react";

export default function StatsCard({ events = [], notes = [] }) {
  const totalEvents = events.length;
  const errorEvents = events.filter((e) => Number(e.status_code) >= 400).length;
  const successEvents = events.filter((e) => Number(e.status_code) < 400).length;
  const totalNotes = notes.length;

  return (
    <section aria-label="시스템 요약 통계" className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
      <div className="p-3.5 rounded bg-surface border border-border shadow-elevation-1">
        <div className="flex items-center justify-between text-muted text-xs mb-1">
          <span>전체 수집 요청</span>
          <Radio className="w-4 h-4 text-accent" />
        </div>
        <div className="text-xl font-bold text-foreground">{totalEvents}</div>
        <div className="text-[11px] text-muted mt-0.5">수집된 전체 HTTP 이벤트</div>
      </div>

      <div className="p-3.5 rounded bg-surface border border-border shadow-elevation-1">
        <div className="flex items-center justify-between text-muted text-xs mb-1">
          <span>정상 처리 (2xx/3xx)</span>
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
        </div>
        <div className="text-xl font-bold text-emerald-400">{successEvents}</div>
        <div className="text-[11px] text-muted mt-0.5">성공 및 리다이렉트 응답</div>
      </div>

      <div className="p-3.5 rounded bg-surface border border-border shadow-elevation-1">
        <div className="flex items-center justify-between text-muted text-xs mb-1">
          <span>오류 요청 (4xx/5xx)</span>
          <AlertTriangle className="w-4 h-4 text-amber-400" />
        </div>
        <div className="text-xl font-bold text-amber-400">{errorEvents}</div>
        <div className="text-[11px] text-muted mt-0.5">클라이언트 및 서버 오류 (400 이상)</div>
      </div>

      <div className="p-3.5 rounded bg-surface border border-border shadow-elevation-1">
        <div className="flex items-center justify-between text-muted text-xs mb-1">
          <span>작성된 관찰 메모</span>
          <FileText className="w-4 h-4 text-sky-400" />
        </div>
        <div className="text-xl font-bold text-sky-400">{totalNotes}</div>
        <div className="text-[11px] text-muted mt-0.5">운영자 기록 누적</div>
      </div>
    </section>
  );
}
