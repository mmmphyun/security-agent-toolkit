import { AlertTriangle, Trash2, X } from "lucide-react";

export default function ConfirmModal({
  isOpen,
  title = "메모 삭제 확인",
  message = "이 메모를 정말 삭제하시겠습니까? 삭제된 메모는 복구할 수 없습니다.",
  note = null,
  onConfirm,
  onCancel,
  loading = false,
}) {
  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-modal-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-sm"
    >
      <div className="w-full max-w-sm rounded-lg bg-surface border border-border p-5 shadow-elevation-4">
        <header className="flex items-start justify-between gap-3 mb-3">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-full flex items-center justify-center bg-red-950/60 border border-red-800/40 text-red-400">
              <AlertTriangle className="w-4 h-4" />
            </div>
            <h3 id="confirm-modal-title" className="text-sm font-bold text-foreground">
              {title}
            </h3>
          </div>
          <button
            type="button"
            onClick={onCancel}
            disabled={loading}
            className="p-1 rounded text-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
            aria-label="닫기"
          >
            <X className="w-4 h-4" />
          </button>
        </header>

        <p className="text-xs text-muted leading-relaxed mb-4">
          {message}
        </p>

        {note && (
          <div className="mb-4 p-2.5 rounded bg-background border border-border text-xs">
            <span className="font-mono text-accent text-[11px] font-semibold mr-1.5">
              #{note.id}
            </span>
            <span className="font-medium text-foreground">{note.title}</span>
          </div>
        )}

        <footer className="flex items-center justify-end gap-2 pt-2 border-t border-border">
          <button
            type="button"
            onClick={onCancel}
            disabled={loading}
            className="px-3 py-1.5 text-xs font-medium rounded bg-background border border-border text-muted hover:text-foreground transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
          >
            취소 (보존)
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded bg-red-600 text-white hover:bg-red-500 disabled:opacity-50 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-400"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>{loading ? "삭제 중..." : "삭제 확정"}</span>
          </button>
        </footer>
      </div>
    </div>
  );
}
