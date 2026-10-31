export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, any>;
}

const BASE_URL = "http://localhost:8000/api/v1";

export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = localStorage.getItem("subscriptiq_access_token");
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    // Attempt token refresh if available
    const refreshToken = localStorage.getItem("subscriptiq_refresh_token");
    if (refreshToken && !endpoint.includes("/auth/refresh")) {
      try {
        const refreshRes = await fetch(`${BASE_URL}/auth/refresh`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });
        if (refreshRes.ok) {
          const data = await refreshRes.json();
          localStorage.setItem("subscriptiq_access_token", data.access_token);
          localStorage.setItem("subscriptiq_refresh_token", data.refresh_token);
          // Retry original request with new token
          headers["Authorization"] = `Bearer ${data.access_token}`;
          const retryRes = await fetch(`${BASE_URL}${endpoint}`, {
            ...options,
            headers,
          });
          if (!retryRes.ok) {
            const errData = await retryRes.json();
            throw errData.error || { code: "HTTP_ERROR", message: retryRes.statusText };
          }
          return retryRes.json();
        }
      } catch (e) {
        localStorage.removeItem("subscriptiq_access_token");
        localStorage.removeItem("subscriptiq_refresh_token");
        localStorage.removeItem("subscriptiq_user");
      }
    }
  }

  if (!response.ok) {
    let errPayload: ApiError = {
      code: `HTTP_${response.status}`,
      message: response.statusText,
    };
    try {
      const data = await response.json();
      if (data.error) {
        errPayload = data.error;
      }
    } catch (_) {}
    throw errPayload;
  }

  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}
