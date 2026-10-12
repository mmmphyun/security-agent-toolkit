import { requestJson } from "./client.js";

export function loginUser(username, password) {
  return requestJson("/api/auth/login", "POST", { username, password });
}
