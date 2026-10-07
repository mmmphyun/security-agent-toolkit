import { useState, useEffect, useCallback } from "react";
import { fetchMe, logout } from "./api/auth";
import { fetchEvents } from "./api/events";
import {
  fetchNotes,
  fetchNote,
  createNote,
  updateNote,
  deleteNote,
} from "./api/notes";
import LoginForm from "./components/LoginForm";
import Navbar from "./components/Navbar";
import StatsCard from "./components/StatsCard";
import EventList from "./components/EventList";
import NoteList from "./components/NoteList";
import NoteDetail from "./components/NoteDetail";
import NoteForm from "./components/NoteForm";
import ConfirmModal from "./components/ConfirmModal";
import { RefreshCw } from "lucide-react";

export default function App() {
  const [user, setUser] = useState(null);
  const [authInitialized, setAuthInitialized] = useState(false);

  // 이벤트 상태
  const [events, setEvents] = useState([]);
  const [eventsLoading, setEventsLoading] = useState(false);
  const [eventsError, setEventsError] = useState(null);

  // 메모 목록 상태
  const [notes, setNotes] = useState([]);
  const [notesLoading, setNotesLoading] = useState(false);
  const [notesError, setNotesError] = useState(null);

  // 메모 상세 / 편집 상태
  const [selectedNoteId, setSelectedNoteId] = useState(null);
  const [selectedNote, setSelectedNote] = useState(null);
  const [noteDetailLoading, setNoteDetailLoading] = useState(false);
  const [noteDetailError, setNoteDetailError] = useState(null);

  // 모드 상태: 'view' | 'create' | 'edit'
  const [noteMode, setNoteMode] = useState("view");
  const [editingNote, setEditingNote] = useState(null);
  const [formSubmitting, setFormSubmitting] = useState(false);

  // 삭제 모달 상태
  const [deletingNote, setDeletingNote] = useState(null);
  const [deleteSubmitting, setDeleteSubmitting] = useState(false);

  // 새로고침 인디케이터
  const [refreshing, setRefreshing] = useState(false);

  // 1. 초기 세션 및 CSRF 토큰 동기화
  useEffect(() => {
    async function initAuth() {
      try {
        const res = await fetchMe();
        if (res && res.user) {
          setUser(res.user);
        }
      } catch {
        // 미로그인 상태는 정상적인 진입 흐름
      } finally {
        setAuthInitialized(true);
      }
    }
    initAuth();
  }, []);

  // 2. 이벤트 목록 조회
  const loadEvents = useCallback(async () => {
    setEventsLoading(true);
    setEventsError(null);
    try {
      const data = await fetchEvents();
      setEvents(data);
    } catch (err) {
      setEventsError(err.message || "요청 기록을 불러오지 못했습니다.");
    } finally {
      setEventsLoading(false);
    }
  }, []);

  // 3. 메모 목록 조회
  const loadNotes = useCallback(async () => {
    setNotesLoading(true);
    setNotesError(null);
    try {
      const data = await fetchNotes();
      setNotes(data);
      return data;
    } catch (err) {
      setNotesError(err.message || "관찰 메모 목록을 불러오지 못했습니다.");
      return [];
    } finally {
      setNotesLoading(false);
    }
  }, []);

  // 4. 특정 메모 상세 조회
  const loadNoteDetail = useCallback(async (id) => {
    if (!id) return;
    setNoteDetailLoading(true);
    setNoteDetailError(null);
    try {
      const note = await fetchNote(id);
      setSelectedNote(note);
    } catch (err) {
      setNoteDetailError(err.message || "메모 상세를 불러오지 못했습니다.");
      setSelectedNote(null);
    } finally {
      setNoteDetailLoading(false);
    }
  }, []);

  // 로그인 상태가 되면 데이터 로드
  useEffect(() => {
    if (user) {
      loadEvents();
      loadNotes().then((loaded) => {
        if (loaded && loaded.length > 0 && !selectedNoteId) {
          setSelectedNoteId(loaded[0].id);
          loadNoteDetail(loaded[0].id);
        }
      });
    } else {
      setEvents([]);
      setNotes([]);
      setSelectedNote(null);
      setSelectedNoteId(null);
      setNoteMode("view");
    }
  }, [user, loadEvents, loadNotes, loadNoteDetail]);

  // 메모 선택 핸들러
  const handleSelectNote = (id) => {
    setSelectedNoteId(id);
    setNoteMode("view");
    loadNoteDetail(id);
  };

  // 전체 새로고침 핸들러
  const handleRefreshAll = async () => {
    setRefreshing(true);
    await Promise.all([
      loadEvents(),
      loadNotes().then((loadedNotes) => {
        if (selectedNoteId) {
          const stillExists = loadedNotes.some((n) => n.id === selectedNoteId);
          if (stillExists) {
            loadNoteDetail(selectedNoteId);
          } else if (loadedNotes.length > 0) {
            setSelectedNoteId(loadedNotes[0].id);
            loadNoteDetail(loadedNotes[0].id);
          } else {
            setSelectedNoteId(null);
            setSelectedNote(null);
          }
        }
      }),
    ]);
    setRefreshing(false);
  };

  // 로그아웃 핸들러
  const handleLogout = async () => {
    try {
      await logout();
    } catch {
      // 오류 여부와 무관하게 클라이언트 상태 정리
    }
    setUser(null);
    setSelectedNote(null);
    setSelectedNoteId(null);
    setNoteMode("view");
  };

  // 메모 작성 모드 열기
  const handleOpenCreate = () => {
    setNoteMode("create");
    setEditingNote(null);
  };

  // 메모 수정 모드 열기
  const handleOpenEdit = (note) => {
    setEditingNote(note);
    setNoteMode("edit");
  };

  // 메모 작성/수정 저장
  const handleSaveNote = async ({ title, body }) => {
    setFormSubmitting(true);
    try {
      if (noteMode === "edit" && editingNote) {
        const updated = await updateNote(editingNote.id, title, body);
        await loadNotes();
        setSelectedNote(updated);
        setSelectedNoteId(updated.id);
        setNoteMode("view");
      } else {
        const created = await createNote(title, body);
        await loadNotes();
        setSelectedNote(created);
        setSelectedNoteId(created.id);
        setNoteMode("view");
      }
    } finally {
      setFormSubmitting(false);
    }
  };

  // 메모 폼 취소
  const handleCancelForm = () => {
    setNoteMode("view");
    setEditingNote(null);
  };

  // 메모 삭제 모달 열기
  const handleOpenDelete = (note) => {
    setDeletingNote(note);
  };

  // 메모 삭제 확정
  const handleConfirmDelete = async () => {
    if (!deletingNote) return;
    setDeleteSubmitting(true);
    try {
      await deleteNote(deletingNote.id);
      setDeletingNote(null);
      const reloadedNotes = await loadNotes();
      if (selectedNoteId === deletingNote.id) {
        if (reloadedNotes.length > 0) {
          setSelectedNoteId(reloadedNotes[0].id);
          loadNoteDetail(reloadedNotes[0].id);
        } else {
          setSelectedNoteId(null);
          setSelectedNote(null);
        }
      }
    } catch (err) {
      alert(err.message || "메모 삭제에 실패했습니다.");
    } finally {
      setDeleteSubmitting(false);
    }
  };

  // 1. 초기 인증 확인 중
  if (!authInitialized) {
    return (
      <main className="min-h-screen flex items-center justify-center bg-background text-muted">
        <div className="flex items-center gap-2 text-xs">
          <RefreshCw className="w-4 h-4 animate-spin text-accent" />
          <span>관제 시스템 환경을 초기화하는 중입니다...</span>
        </div>
      </main>
    );
  }

  // 2. 미로그인 시 로그인 화면 렌더링
  if (!user) {
    return <LoginForm onLoginSuccess={(loggedInUser) => setUser(loggedInUser)} />;
  }

  // 3. 로그인 완료 시 대시보드 콕핏 렌더링
  return (
    <div className="min-h-screen flex flex-col bg-background text-foreground">
      <Navbar
        username={user.username}
        onRefreshAll={handleRefreshAll}
        onLogout={handleLogout}
        refreshing={refreshing}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 flex flex-col">
        {/* 요약 통계 카드 */}
        <StatsCard events={events} notes={notes} />

        {/* 2-컬럼 고밀도 관제 콕핏 그리드 */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 flex-1 items-start">
          {/* 좌측: 실시간 요청 이벤트 로그 테이블 (7 cols) */}
          <section className="lg:col-span-7 h-full flex flex-col" aria-label="요청 로그 관제">
            <EventList
              events={events}
              loading={eventsLoading}
              error={eventsError}
              onRetry={loadEvents}
            />
          </section>

          {/* 우측: 관찰 메모 패널 (5 cols: 목록 + 상세/작성) */}
          <section
            className="lg:col-span-5 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-1 gap-4"
            aria-label="관찰 메모 관리"
          >
            {/* 메모 목록 카드 */}
            <div className="p-4 rounded-lg bg-surface border border-border shadow-elevation-2 min-h-[220px]">
              <NoteList
                notes={notes}
                selectedNoteId={selectedNoteId}
                onSelectNote={handleSelectNote}
                onOpenCreate={handleOpenCreate}
                loading={notesLoading}
                error={notesError}
                onRetry={loadNotes}
              />
            </div>

            {/* 메모 상세 또는 작성/수정 폼 카드 */}
            <div className="p-4 rounded-lg bg-surface border border-border shadow-elevation-2 min-h-[260px]">
              {noteMode === "create" || noteMode === "edit" ? (
                <NoteForm
                  initialNote={editingNote}
                  onSave={handleSaveNote}
                  onCancel={handleCancelForm}
                  submitting={formSubmitting}
                />
              ) : (
                <NoteDetail
                  note={selectedNote}
                  loading={noteDetailLoading}
                  error={noteDetailError}
                  onEdit={handleOpenEdit}
                  onOpenDelete={handleOpenDelete}
                  onRetry={() => loadNoteDetail(selectedNoteId)}
                />
              )}
            </div>
          </section>
        </div>
      </main>

      {/* 삭제 확인/취소 모달 */}
      <ConfirmModal
        isOpen={Boolean(deletingNote)}
        note={deletingNote}
        onConfirm={handleConfirmDelete}
        onCancel={() => setDeletingNote(null)}
        loading={deleteSubmitting}
      />
    </div>
  );
}
