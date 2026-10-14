import { useState } from "react";

export default function NoteForm(props) {
  const [title, setTitle] = useState(props.note.title);
  const [body, setBody] = useState(props.note.body);

  function handleSubmit(event) {
    event.preventDefault();
    props.onSave(title, body);
  }

  return (
    <section className="panel">
      <h2>{props.heading}</h2>
      <form onSubmit={handleSubmit}>
        <label>제목<input value={title} onChange={function (event) { setTitle(event.target.value); }} /></label>
        <label>내용<textarea value={body} onChange={function (event) { setBody(event.target.value); }} /></label>
        <div className="actions">
          <button className="primary" type="submit" disabled={props.busy}>저장</button>
          <button type="button" onClick={props.onCancel} disabled={props.busy}>취소</button>
        </div>
      </form>
    </section>
  );
}
