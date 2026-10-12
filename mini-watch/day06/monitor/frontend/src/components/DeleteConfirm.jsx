export default function DeleteConfirm(props) {
  return (
    <section className="panel">
      <h2>메모 삭제</h2>
      <p>“{props.note.title}” 메모를 삭제합니다. 삭제한 메모는 되돌릴 수 없습니다.</p>
      <div className="actions">
        <button className="danger" onClick={props.onConfirm} disabled={props.busy}>삭제 확인</button>
        <button onClick={props.onCancel} disabled={props.busy}>취소</button>
      </div>
    </section>
  );
}
