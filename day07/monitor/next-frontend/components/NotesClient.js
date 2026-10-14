"use client";

import { useState } from "react";
import { getNotes, createNote, updateNote, removeNote } from "../api/notes";

export default function NotesClient() {
  const [notes, setNotes] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function handleLoad() {
    setError("");
    setMessage("");
    setBusy(true);
    try {
      const result = await getNotes();
      setNotes(result.notes);
    } catch (error) {
      setError(error.message);
    } finally {
      setBusy(false);
    }
  }

  function startEdit(note) {
    setEditingId(note.id);
    setTitle(note.title);
    setBody(note.body);
    setError("");
    setMessage("");
  }

  function resetForm() {
    setEditingId(null);
    setTitle("");
    setBody("");
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setMessage("");
    setBusy(true);
    try {
      if (editingId === null) {
        const result = await createNote(title, body);
        setNotes([...notes, result.note]);
        setMessage("메모를 등록했습니다.");
      } else {
        const result = await updateNote(editingId, title, body);
        setNotes(notes.map((note) => {
          if (note.id === editingId) {
            return result.note;
          }
          return note;
        }));
        setMessage("메모를 수정했습니다.");
      }
      resetForm();
    } catch (error) {
      setError(error.message);
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete(note) {
    if (!window.confirm('"' + note.title + '" 메모를 삭제할까요?')) {
      return;
    }
    setError("");
    setMessage("");
    setBusy(true);
    try {
      await removeNote(note.id);
      setNotes(notes.filter((item) => item.id !== note.id));
      if (editingId === note.id) {
        resetForm();
      }
      setMessage("메모를 삭제했습니다.");
    } catch (error) {
      setError(error.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <button onClick={handleLoad} disabled={busy}>목록 불러오기</button>
      {busy && <p>처리 중입니다.</p>}
      {error && <p className="error" role="alert">{error}</p>}
      {message && <p className="message" role="status">{message}</p>}
      {notes === null && <p>목록 불러오기를 눌러 메모를 확인하세요.</p>}
      {notes !== null && (
        <div>
          <form onSubmit={handleSubmit}>
            <h2>{editingId === null ? "새 메모" : "메모 수정"}</h2>
            <fieldset disabled={busy}>
              <label>제목
                <input value={title} onChange={(event) => setTitle(event.target.value)} />
              </label>
              <label>내용
                <textarea value={body} onChange={(event) => setBody(event.target.value)} />
              </label>
              <div className="actions">
                <button type="submit">{editingId === null ? "등록" : "수정 저장"}</button>
                {editingId !== null && <button type="button" onClick={resetForm}>수정 취소</button>}
              </div>
            </fieldset>
          </form>
          <p>메모 {notes.length}개</p>
          {notes.length === 0 && <p>아직 메모가 없습니다.</p>}
          {notes.map((note) => (
            <article key={note.id}>
              <h2>{note.title}</h2>
              <p className="note-body">{note.body}</p>
              <div className="actions">
                <button onClick={() => startEdit(note)} disabled={busy}>수정</button>
                <button onClick={() => handleDelete(note)} disabled={busy}>삭제</button>
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
