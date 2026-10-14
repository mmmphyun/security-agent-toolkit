import { request } from "./client";

export async function fetchNotes() {
  const data = await request("/api/notes");
  return data.notes || [];
}

export async function fetchNote(noteId) {
  const data = await request(`/api/notes/${noteId}`);
  return data.note;
}

export async function createNote(title, body) {
  const data = await request("/api/notes", {
    method: "POST",
    body: JSON.stringify({ title, body }),
  });
  return data.note;
}

export async function updateNote(noteId, title, body) {
  const data = await request(`/api/notes/${noteId}`, {
    method: "PUT",
    body: JSON.stringify({ title, body }),
  });
  return data.note;
}

export async function deleteNote(noteId) {
  const data = await request(`/api/notes/${noteId}`, {
    method: "DELETE",
  });
  return data;
}
