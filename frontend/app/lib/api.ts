export async function apiFetch(path: string, opts?: RequestInit) {
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  const url = path;

  const res = await fetch(url, {
    ...opts,
    headers: {
      "Content-Type": "application/json",
      Authorization: token ? `Bearer ${token}` : "",
      ...opts?.headers,
    },
  });

  if (!res.ok) {
    if (res.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      localStorage.removeItem("user");
      if (!window.location.pathname.startsWith("/login") && window.location.pathname !== "/") {
        window.location.href = "/?expired=1";
      }
      throw new Error("Session expired. Please log in again.");
    }

    const errorText = await res.text().catch(() => "Request failed");
    try {
      const parsed = JSON.parse(errorText);
      throw new Error(parsed.detail || errorText);
    } catch (e: any) {
      if (e.message && e.message !== errorText) throw e;
      throw new Error(errorText);
    }
  }

  return res.json();
}
