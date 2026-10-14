import { useEffect, useState } from "react";
import { getNotes, getNote, createNote, updateNote, removeNote } from "../api/notes.js";
import { getEvents } from "../api/events.js";
import NoteList from "./NoteList.jsx";
import NoteDetail from "./NoteDetail.jsx";
import NoteForm from "./NoteForm.jsx";
import DeleteConfirm from "./DeleteConfirm.jsx";
import EventList from "./EventList.jsx";

export default function Dashboard(props) {
  const [notes, setNotes] = useState([]);
  const [events, setEvents] = useState([]);
  const [selected, setSelected] = useState(null);
  const [screen, setScreen] = useState("detail");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");

  async function loadData() {
    props.onClearError();
    setLoading(true);
    try {
      const notesData = await getNotes();
      const eventsData = await getEvents();
      setNotes(notesData.notes);
      setEvents(eventsData.events);
    } catch (error) {
      props.onError(error);
    } finally {
      setLoading(false);
    }
  }

  useEffect(function () {
    loadData();
  }, []);

  async function selectNote(id) {
    props.onClearError();
    if (busy) return;
    setMessage("");
    try {
      const data = await getNote(id);
      setSelected(data.note);
      setScreen("detail");
    } catch (error) {
      setSelected(null);
      setScreen("detail");
      props.onError(error);
    }
  }

  function startNew() {
    props.onClearError();
    setMessage("");
    setScreen("new");
  }

  async function saveNote(title, body) {
    props.onClearError();
    setBusy(true);
    setMessage("");
    try {
      let data;
      if (screen === "new") {
        data = await createNote(title, body);
      } else {
        data = await updateNote(selected.id, title, body);
      }
      setSelected(data.note);
      setScreen("detail");
      setMessage("메모를 저장했습니다.");
      await loadData();
    } catch (error) {
      props.onError(error);
    } finally {
      setBusy(false);
    }
  }

  async function deleteNote() {
    props.onClearError();
    setBusy(true);
    setMessage("");
    try {
      const data = await removeNote(selected.id);
      setSelected(null);
      setScreen("detail");
      setMessage(data.message);
      await loadData();
    } catch (error) {
      props.onError(error);
    } finally {
      setBusy(false);
    }
  }

  let content;
  if (screen === "new") {
    content = <NoteForm key="new" heading="새 관찰 메모" note={{ title: "", body: "" }} onSave={saveNote} onCancel={function () { setScreen("detail"); }} busy={busy} />;
  } else if (screen === "edit") {
    content = <NoteForm key="edit" heading="메모 수정" note={selected} onSave={saveNote} onCancel={function () { setScreen("detail"); }} busy={busy} />;
  } else if (screen === "delete") {
    content = <DeleteConfirm note={selected} onConfirm={deleteNote} onCancel={function () { setScreen("detail"); }} busy={busy} />;
  } else {
    content = <NoteDetail note={selected} onEdit={function () { setScreen("edit"); }} onDelete={function () { setScreen("delete"); }} />;
  }

  return (
    <div>
      <div className="actions">
        <button className="primary" onClick={startNew} disabled={busy}>새 메모</button>
        <button onClick={loadData} disabled={loading || busy}>목록 새로고침</button>
      </div>
      {loading && <p role="status">자료를 불러오고 있습니다.</p>}
      {message && <p className="notice" role="status">{message}</p>}
      <div className="workspace">
        <NoteList notes={notes} onSelect={selectNote} />
        {content}
      </div>
      <EventList events={events} />
    </div>
  );
}
