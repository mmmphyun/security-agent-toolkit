import { request, setCsrfToken } from "./client";

export async function fetchMe() {
  const data = await request("/api/auth/me");
  if (data && data.csrf_token) {
    setCsrfToken(data.csrf_token);
  }
  return data;
}

export async function login(username, password) {
  const data = await request("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
  if (data && data.csrf_token) {
    setCsrfToken(data.csrf_token);
  }
  return data;
}

export async function logout() {
  const data = await request("/api/auth/logout", {
    method: "POST",
  });
  if (data && data.csrf_token) {
    setCsrfToken(data.csrf_token);
  }
  return data;
}
