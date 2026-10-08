"use client";

import { useState } from "react";

const INITIAL_NOTES = [
  { id: 1, text: "Next.js 컴포넌트 구조 이해하기" },
  { id: 2, text: "Client Component와 useState 실습" },
];

export default function Notes() {
  const [notes, setNotes] = useState(INITIAL_NOTES);
  const [inputText, setInputText] = useState("");
  const [editingId, setEditingId] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmed = inputText.trim();

    if (!trimmed) {
      setErrorMessage("메모 내용을 1자 이상 입력해주세요 (공백 불가).");
      return;
    }
    setErrorMessage("");

    if (editingId !== null) {
      // 수정 모드: 해당 ID의 메모만 변경
      setNotes((prev) =>
        prev.map((item) => (item.id === editingId ? { ...item, text: trimmed } : item))
      );
      setEditingId(null);
      setInputText("");
    } else {
      // 등록 모드: 고유 ID 생성 후 목록 추가
      const newNote = {
        id: Date.now(),
        text: trimmed,
      };
      setNotes((prev) => [...prev, newNote]);
      setInputText("");
    }
  };

  const startEdit = (note) => {
    setEditingId(note.id);
    setInputText(note.text);
    setErrorMessage("");
  };

  const cancelEdit = () => {
    setEditingId(null);
    setInputText("");
    setErrorMessage("");
  };

  const handleDelete = (id) => {
    const confirmed = window.confirm("해당 메모를 삭제하시겠습니까?");
    if (!confirmed) {
      return;
    }

    setNotes((prev) => prev.filter((item) => item.id !== id));

    // 수정 중인 대상을 삭제하면 폼 초기화
    if (editingId === id) {
      setEditingId(null);
      setInputText("");
      setErrorMessage("");
    }
  };

  return (
    <div>
      <form onSubmit={handleSubmit} className="card" style={{ marginTop: 0 }}>
        <h3 style={{ marginTop: 0, marginBottom: "12px", fontSize: "16px" }}>
          {editingId !== null ? "메모 수정하기" : "새 메모 작성"}
        </h3>
        <div style={{ display: "flex", gap: "8px" }}>
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="메모를 입력하세요..."
          />
          <button type="submit" className="primary" style={{ flexShrink: 0 }}>
            {editingId !== null ? "수정 저장" : "등록"}
          </button>
          {editingId !== null && (
            <button type="button" onClick={cancelEdit} style={{ flexShrink: 0 }}>
              수정 취소
            </button>
          )}
        </div>
        {errorMessage && (
          <p style={{ color: "#ef4444", fontSize: "13px", margin: "8px 0 0 0" }}>
            {errorMessage}
          </p>
        )}
      </form>

      <div style={{ marginTop: "24px" }}>
        <h3 style={{ fontSize: "16px", marginBottom: "12px" }}>메모 목록 ({notes.length})</h3>
        {notes.length === 0 ? (
          <div
            className="card"
            style={{ textAlign: "center", color: "#64748b", padding: "32px 16px" }}
          >
            등록된 메모가 없습니다. 첫 메모를 등록해보세요!
          </div>
        ) : (
          <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: "10px" }}>
            {notes.map((note) => (
              <li
                key={note.id}
                className="card"
                style={{
                  marginTop: 0,
                  padding: "16px",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                }}
              >
                <span style={{ fontSize: "15px", wordBreak: "break-all" }}>{note.text}</span>
                <div style={{ display: "flex", gap: "8px", flexShrink: 0, marginLeft: "16px" }}>
                  <button onClick={() => startEdit(note)}>수정</button>
                  <button className="danger" onClick={() => handleDelete(note.id)}>
                    삭제
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
