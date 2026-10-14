export default function NoteDetail(props) {
  if (props.note === null) {
    return <section className="panel"><h2>메모 상세</h2><p className="muted">목록에서 제목을 선택해 주세요.</p></section>;
  }
  return (
    <section className="panel">
      <p className="muted">메모 {props.note.id}</p>
      <h2>{props.note.title}</h2>
      <p className="body-text">{props.note.body}</p>
      <div className="actions">
        <button onClick={props.onEdit}>수정</button>
        <button className="danger" onClick={props.onDelete}>삭제</button>
      </div>
    </section>
  );
}
