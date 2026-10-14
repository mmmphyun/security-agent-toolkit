import { requestJson } from "./client.js";

export function getEvents() {
  return requestJson("/api/events");
}
