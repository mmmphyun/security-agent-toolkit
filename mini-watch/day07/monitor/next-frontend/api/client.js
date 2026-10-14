let csrfToken = "";
export async function requestJson(path, method = "GET", data = null) {
  if (method !== "GET" && !csrfToken) {
    const state = await requestJson("/api/auth/me");
    csrfToken = state.csrf_token;
  }
  const options = {
    method,
    headers: { "Content-Type": "application/json" },
    credentials: "same-origin",
  };
  if (method !== "GET") options.headers["X-CSRF-Token"] = csrfToken;
  if (data !== null) options.body = JSON.stringify(data);
  const response = await fetch(path, options);
  let result;
  try { result = await response.json(); }
  catch { throw new Error("API와 연결하지 못했습니다."); }
  if (result.csrf_token) csrfToken = result.csrf_token;
  if (!response.ok) throw new Error(result.error || "요청을 처리하지 못했습니다.");
  return result;
}
