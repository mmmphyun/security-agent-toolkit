import { requestJson } from "./client.js";

export function getNotes() {
  return requestJson("/api/notes");
}

export function getNote(id) {
  return requestJson("/api/notes/" + id);
}

export function createNote(title, body) {
  return requestJson("/api/notes", "POST", { title, body });
}

export function updateNote(id, title, body) {
  return requestJson("/api/notes/" + id, "PUT", { title, body });
}

export function removeNote(id) {
  return requestJson("/api/notes/" + id, "DELETE", null);
}
