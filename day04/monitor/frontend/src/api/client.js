let storedCsrfToken = "";

export function setCsrfToken(token) {
  if (typeof token === "string") {
    storedCsrfToken = token;
  }
}

export function getCsrfToken() {
  return storedCsrfToken;
}

export async function request(url, options = {}) {
  const config = {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  };

  const method = (config.method || "GET").toUpperCase();
  if (["POST", "PUT", "PATCH", "DELETE"].includes(method) && storedCsrfToken) {
    config.headers["X-CSRF-Token"] = storedCsrfToken;
  }

  const response = await fetch(url, config);
  const data = await response.json().catch(() => null);

  if (!response.ok) {
    const message = (data && data.error) || (data && data.message) || `요청 실패 (${response.status})`;
    const error = new Error(message);
    error.status = response.status;
    error.data = data;
    throw error;
  }

  return data;
}
