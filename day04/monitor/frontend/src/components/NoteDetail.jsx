import { Edit3, Trash2, FileText, AlertCircle, RefreshCw } from "lucide-react";

export default function NoteDetail({
  note = null,
  loading = false,
  error = null,
  onEdit,
  onOpenDelete,
  onRetry,
}) {
  if (loading) {
    return (
      <div aria-busy="true" className="flex flex-col items-center justify-center h-full py-16 text-muted gap-2">
        <RefreshCw className="w-5 h-5 animate-spin text-accent" />
        <span className="text-xs">메모 내용을 불러오는 중입니다...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div role="alert" className="flex flex-col items-center justify-center h-full py-16 text-center">
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
    );
  }

  if (!note) {
    return (
      <div className="flex flex-col items-center justify-center h-full py-16 text-center text-muted">
        <FileText className="w-8 h-8 stroke-1 mb-2 opacity-50" />
        <p className="text-xs font-medium text-foreground">선택된 메모가 없습니다.</p>
        <p className="text-[11px] text-muted mt-1 max-w-xs">
          왼쪽 목록에서 확인할 메모를 클릭하면 제목과 본문 상세가 표시됩니다.
        </p>
      </div>
    );
  }

  return (
    <article className="flex flex-col h-full">
      <header className="flex items-start justify-between gap-3 pb-3 mb-4 border-b border-border">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="font-mono text-xs font-semibold px-2 py-0.5 rounded bg-background border border-border text-accent">
              메모 #{note.id}
            </span>
          </div>
          <h3 className="text-base font-bold text-foreground break-words">{note.title}</h3>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <button
            type="button"
            onClick={() => onEdit(note)}
            className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded bg-background border border-border text-foreground hover:bg-surface transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
          >
            <Edit3 className="w-3.5 h-3.5 text-accent" />
            <span>수정</span>
          </button>

          <button
            type="button"
            onClick={() => onOpenDelete(note)}
            className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded bg-red-950/40 border border-red-800/40 text-red-300 hover:bg-red-900/50 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-400"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>삭제</span>
          </button>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto pr-1">
        <div className="p-3.5 rounded bg-background border border-border/80 text-xs leading-relaxed text-foreground/90 whitespace-pre-wrap font-sans">
          {note.body}
        </div>
      </div>
    </article>
  );
}
