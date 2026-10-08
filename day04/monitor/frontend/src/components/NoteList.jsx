import { Plus, FileText, ChevronRight, RefreshCw, AlertCircle } from "lucide-react";

export default function NoteList({
  notes = [],
  selectedNoteId = null,
  onSelectNote,
  onOpenCreate,
  loading = false,
  error = null,
  onRetry,
}) {
  return (
    <div className="flex flex-col h-full">
      <header className="flex items-center justify-between pb-3 mb-2 border-b border-border">
        <div>
          <h2 className="text-sm font-bold text-foreground flex items-center gap-2">
            <FileText className="w-4 h-4 text-accent" />
            <span>관찰 메모 목록</span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-background border border-border text-muted">
              {notes.length}건
            </span>
          </h2>
          <p className="text-[11px] text-muted mt-0.5">이상 징후 및 점검 메모</p>
        </div>

        <button
          type="button"
          onClick={onOpenCreate}
          className="flex items-center gap-1 px-2.5 py-1 text-xs font-semibold rounded bg-accent text-slate-950 hover:opacity-90 transition-opacity focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>메모 작성</span>
        </button>
      </header>

      {/* 4-State */}
      {loading && (
        <div aria-busy="true" className="flex-1 flex flex-col justify-center items-center py-10 text-muted gap-2">
          <RefreshCw className="w-4 h-4 animate-spin text-accent" />
          <span className="text-xs">메모를 불러오는 중입니다...</span>
        </div>
      )}

      {!loading && error && (
        <div role="alert" className="flex-1 flex flex-col justify-center items-center py-8 text-center">
          <AlertCircle className="w-5 h-5 text-red-400 mb-1.5" />
          <p className="text-xs text-red-300 mb-2">{error}</p>
          {onRetry && (
            <button
              type="button"
              onClick={onRetry}
              className="px-2.5 py-1 text-xs rounded bg-background border border-border text-foreground hover:bg-surface focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
            >
              다시 시도
            </button>
          )}
        </div>
      )}

      {!loading && !error && notes.length === 0 && (
        <div className="flex-1 flex flex-col justify-center items-center py-10 text-center text-muted">
          <FileText className="w-7 h-7 stroke-1 mb-2 opacity-50" />
          <p className="text-xs font-medium text-foreground">저장된 메모가 없습니다.</p>
          <p className="text-[11px] text-muted mt-1">상단의 메모 작성 버튼을 눌러 새 메모를 등록하세요.</p>
        </div>
      )}

      {!loading && !error && notes.length > 0 && (
        <ul className="flex-1 divide-y divide-border/60 overflow-y-auto max-h-[460px] pr-1">
          {notes.map((note) => {
            const isSelected = selectedNoteId === note.id;
            return (
              <li key={note.id}>
                <button
                  type="button"
                  onClick={() => onSelectNote(note.id)}
                  className={`w-full text-left py-2.5 px-3 rounded transition-colors flex items-center justify-between gap-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent ${
                    isSelected
                      ? "bg-background border border-accent/40 shadow-elevation-1"
                      : "hover:bg-background/60"
                  }`}
                  aria-selected={isSelected}
                >
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 mb-0.5">
                      <span className="font-mono text-[11px] font-semibold text-accent">
                        #{note.id}
                      </span>
                      <span className="text-xs font-medium text-foreground truncate">
                        {note.title}
                      </span>
                    </div>
                    {note.body && (
                      <p className="text-[11px] text-muted truncate">
                        {note.body}
                      </p>
                    )}
                  </div>
                  <ChevronRight
                    className={`w-3.5 h-3.5 shrink-0 ${
                      isSelected ? "text-accent" : "text-muted"
                    }`}
                  />
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
