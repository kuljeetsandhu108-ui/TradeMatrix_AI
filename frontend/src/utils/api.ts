import axios from "axios";

// If we are on the server (Railway), use the production URL.
// If we are local, use localhost.
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

const api = axios.create({
  baseURL: API_URL,
});

export default api;