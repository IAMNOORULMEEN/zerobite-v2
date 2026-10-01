import axios, {
  AxiosError,
  type AxiosInstance,
  type AxiosRequestConfig,
  type InternalAxiosRequestConfig,
} from "axios";

const baseURL = import.meta.env.VITE_API_URL;

if (!baseURL) {
  console.warn("VITE_API_URL is not set. API calls will use relative URLs.");
}

const REFRESH_STORAGE_KEY = "zerobite.refresh";

// --- Token storage: access in memory, refresh in localStorage ---

let accessToken: string | null = null;

export function setAccessToken(token: string | null): void {
  accessToken = token;
}

export function getAccessToken(): string | null {
  return accessToken;
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_STORAGE_KEY);
}

export function setRefreshToken(token: string | null): void {
  if (token) {
    localStorage.setItem(REFRESH_STORAGE_KEY, token);
  } else {
    localStorage.removeItem(REFRESH_STORAGE_KEY);
  }
}

export function clearTokens(): void {
  accessToken = null;
  localStorage.removeItem(REFRESH_STORAGE_KEY);
}

// --- Axios instance ---

export const api: AxiosInstance = axios.create({
  baseURL,
  timeout: 15_000,
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  if (accessToken) {
    config.headers.set("Authorization", `Bearer ${accessToken}`);
  }
  return config;
});

// --- Single-flight refresh ---

type RetriableConfig = InternalAxiosRequestConfig & { _retry?: boolean };

const AUTH_PATH_PREFIX = "/auth/";
const NON_RETRIABLE_PATHS = [
  "/auth/login/",
  "/auth/refresh/",
  "/auth/register/",
  "/auth/password-reset/",
  "/auth/password-reset/confirm/",
];

let refreshPromise: Promise<string> | null = null;

function shouldAttemptRefresh(url: string | undefined): boolean {
  if (!url) return false;
  if (!url.startsWith(AUTH_PATH_PREFIX) && !url.includes(AUTH_PATH_PREFIX)) {
    return true; // Non-auth endpoint.
  }
  // Auth endpoint: only retry if it's not one of the excluded ones.
  return !NON_RETRIABLE_PATHS.some((p) => url.includes(p));
}

export async function refreshAccessToken(): Promise<string> {
  if (refreshPromise) return refreshPromise;

  const refresh = getRefreshToken();
  if (!refresh) {
    clearTokens();
    throw new Error("No refresh token available.");
  }

  refreshPromise = (async () => {
    try {
      // Use a bare axios call to avoid the response interceptor recursing.
      const response = await axios.post(
        `${baseURL}/auth/refresh/`,
        { refresh },
        { headers: { "Content-Type": "application/json" } },
      );
      const newAccess: string | undefined = response.data?.access;
      const newRefresh: string | undefined = response.data?.refresh;
      if (!newAccess) {
        throw new Error("Refresh response did not include an access token.");
      }
      setAccessToken(newAccess);
      // ROTATE_REFRESH_TOKENS=True on the backend, so persist the rotated token.
      if (newRefresh) {
        setRefreshToken(newRefresh);
      }
      return newAccess;
    } catch (error) {
      clearTokens();
      throw error;
    } finally {
      refreshPromise = null;
    }
  })();

  return refreshPromise;
}

function redirectToLogin(): void {
  // Preserve current path so login can bounce the user back.
  const current = window.location.pathname + window.location.search;
  const target = current && current !== "/login" ? `?next=${encodeURIComponent(current)}` : "";
  window.location.assign(`/login${target}`);
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as RetriableConfig | undefined;

    if (
      error.response?.status === 401 &&
      original &&
      !original._retry &&
      shouldAttemptRefresh(original.url)
    ) {
      original._retry = true;
      try {
        const newAccess = await refreshAccessToken();
        original.headers.set("Authorization", `Bearer ${newAccess}`);
        return api.request(original as AxiosRequestConfig);
      } catch {
        redirectToLogin();
        return Promise.reject(error);
      }
    }

    return Promise.reject(error);
  },
);

export default api;
