import axios from "axios";

/**
 * Axios instance pre-configured to point at the FastAPI backend.
 * All API helper functions in src/api/endpoints.ts use this client.
 */
export const apiClient = axios.create({
  baseURL: "http://localhost:8000",
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 30000, // 30s — YOLOv8 inference can take a few seconds
});
