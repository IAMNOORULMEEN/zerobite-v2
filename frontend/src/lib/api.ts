import axios, { type AxiosInstance } from "axios";

const baseURL = import.meta.env.VITE_API_URL;

if (!baseURL) {
  // Fail loud in dev; misconfig in prod should be caught by the browser console too.
  console.warn("VITE_API_URL is not set. API calls will use relative URLs.");
}

export const api: AxiosInstance = axios.create({
  baseURL,
  timeout: 15_000,
  headers: {
    "Content-Type": "application/json",
  },
});

export default api;
