const API_BASE = "";

function getToken(): string | null {
  return sessionStorage.getItem("nanobot_admin_token");
}

export async function api<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...options.headers,
  };
  if (token) {
    (headers as Record<string, string>)["Authorization"] = `Bearer ${token}`;
  }
  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (res.status === 401) {
    sessionStorage.removeItem("nanobot_admin_token");
    window.location.href = "/";
    throw new Error("Unauthorized");
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || String(err) || res.statusText);
  }
  if (res.status === 204 || res.headers.get("content-length") === "0") {
    return undefined as T;
  }
  return res.json();
}

export async function login(token: string): Promise<{ ok: boolean }> {
  const res = await fetch(`${API_BASE}/api/admin/auth`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Invalid token");
  }
  return res.json();
}

export async function health(): Promise<{ status: string; admin_configured: boolean }> {
  return api("/api/admin/health");
}

export const configApi = {
  get: () => api<Record<string, unknown>>("/api/admin/config"),
  patch: (body: Record<string, unknown>) =>
    api<Record<string, unknown>>("/api/admin/config", { method: "PATCH", body: JSON.stringify(body) }),
};

export const workspaceApi = {
  listFiles: () => api<{ name: string; exists: boolean }[]>("/api/admin/workspace/files"),
  getFile: (filename: string) =>
    api<{ name: string; content: string }>(`/api/admin/workspace/files/${filename}`),
  putFile: (filename: string, content: string) =>
    api<{ name: string; ok: boolean }>(`/api/admin/workspace/files/${filename}`, {
      method: "PUT",
      body: JSON.stringify({ content }),
    }),
};

export const skillsApi = {
  list: () => api<{ name: string; path: string; source: string }[]>("/api/admin/skills"),
  get: (name: string) =>
    api<{ name: string; content: string; source: string }>(`/api/admin/skills/${name}`),
  put: (name: string, content: string) =>
    api<{ name: string; ok: boolean }>(`/api/admin/skills/${name}`, {
      method: "PUT",
      body: JSON.stringify({ content }),
    }),
};

export const envApi = {
  list: () => api<{ key: string; set: boolean; masked: string }[]>("/api/admin/env"),
};
