import { useState, useEffect } from "react";
import { Save, X, AlertCircle } from "lucide-react";

export default function NoteForm({
  initialNote = null,
  onSave,
  onCancel,
  submitting = false,
}) {
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [error, setError] = useState(null);

  const isEditing = Boolean(initialNote && initialNote.id);

  useEffect(() => {
    if (initialNote) {
      setTitle(initialNote.title || "");
      setBody(initialNote.body || "");
    } else {
      setTitle("");
      setBody("");
    }
    setError(null);
  }, [initialNote]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    const trimmedTitle = title.trim();
    const trimmedBody = body.trim();

    if (!trimmedTitle || !trimmedBody) {
      setError("제목과 내용을 모두 입력해 주세요. (공백 불가)");
      return;
    }

    try {
      await onSave({
        title: trimmedTitle,
        body: trimmedBody,
      });
    } catch (err) {
      setError(err.message || "메모 저장 요청에 실패했습니다.");
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col h-full" role="form" aria-label="메모 작성 및 수정 폼">
      <header className="flex items-center justify-between pb-3 mb-4 border-b border-border">
        <h3 className="text-sm font-bold text-foreground">
          {isEditing ? `메모 #${initialNote.id} 수정` : "새 관찰 메모 작성"}
        </h3>
        <button
          type="button"
          onClick={onCancel}
          disabled={submitting}
          className="p-1 rounded text-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
          aria-label="닫기"
        >
          <X className="w-4 h-4" />
        </button>
      </header>

      {error && (
        <div
          role="alert"
          className="mb-3 p-2.5 rounded flex items-center gap-2 text-xs bg-background border border-red-500/30 text-red-400"
        >
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <div className="space-y-3 flex-1 flex flex-col">
        <div>
          <label htmlFor="note-title" className="block text-xs font-medium mb-1 text-muted">
            제목
          </label>
          <input
            id="note-title"
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="예: 없는 게시글 요청 확인"
            disabled={submitting}
            className="w-full px-3 py-1.5 text-xs rounded bg-background border border-border text-foreground placeholder:text-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
          />
        </div>

        <div className="flex-1 flex flex-col">
          <label htmlFor="note-body" className="block text-xs font-medium mb-1 text-muted">
            내용
          </label>
          <textarea
            id="note-body"
            rows={8}
            value={body}
            onChange={(e) => setBody(e.target.value)}
            placeholder="예: 요청 경로와 404 응답을 확인했다."
            disabled={submitting}
            className="w-full flex-1 px-3 py-2 text-xs rounded bg-background border border-border text-foreground placeholder:text-muted resize-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
          />
        </div>
      </div>

      <footer className="flex items-center justify-end gap-2 pt-3 mt-4 border-t border-border">
        <button
          type="button"
          onClick={onCancel}
          disabled={submitting}
          className="px-3 py-1.5 text-xs font-medium rounded bg-background border border-border text-muted hover:text-foreground transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
        >
          취소
        </button>
        <button
          type="submit"
          disabled={submitting}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded bg-accent text-slate-950 hover:opacity-90 disabled:opacity-50 transition-opacity focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
        >
          <Save className="w-3.5 h-3.5" />
          <span>{submitting ? "저장 중..." : isEditing ? "수정 완료" : "작성 완료"}</span>
        </button>
      </footer>
    </form>
  );
}
