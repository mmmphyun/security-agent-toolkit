import Notes from "@/components/Notes";

export default function NotesPage() {
  return (
    <div>
      <h1 style={{ fontSize: "24px", fontWeight: "bold", marginBottom: "8px" }}>메모 관리</h1>
      <p style={{ color: "#64748b", margin: "0 0 20px 0" }}>
        React state로 동작하며 새로고침 시 초기 메모 목록으로 복원됩니다.
      </p>
      <Notes />
    </div>
  );
}
