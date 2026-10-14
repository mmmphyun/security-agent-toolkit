import { requestJson } from "./client";

export function getNotes() {
  return requestJson("/api/notes");
}

export function createNote(title, body) {
  return requestJson("/api/notes", "POST", { title, body });
}

export function updateNote(id, title, body) {
  return requestJson("/api/notes/" + id, "PUT", { title, body });
}

export function removeNote(id) {
  return requestJson("/api/notes/" + id, "DELETE");
}
