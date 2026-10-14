export default function NoteList(props) {
  return (
    <section className="panel">
      <h2>관찰 메모</h2>
      {props.notes.length === 0 && <p className="muted">아직 관찰 메모가 없습니다.</p>}
      <ul className="note-list">
        {props.notes.map(function (note) {
          return (
            <li key={note.id}>
              <span className="number">{note.id}</span>
              <button className="link" onClick={function () { props.onSelect(note.id); }}>{note.title}</button>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
