import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

const api = axios.create({ baseURL: BASE_URL });

// --- auth token handling (JWT, silent refresh) ---
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

let refreshQueue = [];
let isRefreshing = false;

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      if (isRefreshing) {
        return new Promise((resolve) => {
          refreshQueue.push((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            resolve(api(originalRequest));
          });
        });
      }

      isRefreshing = true;
      try {
        const refresh = localStorage.getItem("refresh_token");
        const { data } = await axios.post(`${BASE_URL}/token/refresh/`, {
          refresh,
        });
        localStorage.setItem("access_token", data.access);
        refreshQueue.forEach((cb) => cb(data.access));
        refreshQueue = [];
        originalRequest.headers.Authorization = `Bearer ${data.access}`;
        return api(originalRequest);
      } catch (refreshError) {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        window.location.href = "/login";
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }
    return Promise.reject(error);
  }
);

// Normalizes DRF's paginated {results: [...]} shape to a plain array.
export const toArray = (data) => (Array.isArray(data) ? data : data?.results || []);

// --- Auth ---
export const login = (username, password) =>
  api.post("/token/", { username, password }).then((res) => {
    localStorage.setItem("access_token", res.data.access);
    localStorage.setItem("refresh_token", res.data.refresh);
    return res.data;
  });

export const logout = () => {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
};

// --- Patients ---
export const getPatients = (params = {}) =>
  api.get("/patients/", { params }).then((res) => toArray(res.data));

export const getPatient = (id) => api.get(`/patients/${id}/`).then((res) => res.data);

export const createPatient = (payload) =>
  api.post("/patients/", payload).then((res) => res.data);

export const updatePatient = (id, payload) =>
  api.patch(`/patients/${id}/`, payload).then((res) => res.data);

export const deletePatient = (id) => api.delete(`/patients/${id}/`);

// --- Documents ---
export const getDocuments = (params = {}) =>
  api.get("/documents/", { params }).then((res) => toArray(res.data));

export const getDocument = (id) =>
  api.get(`/documents/${id}/`).then((res) => res.data);

export const uploadDocument = (formData, onUploadProgress) =>
  api
    .post("/documents/", formData, {
      headers: { "Content-Type": "multipart/form-data" },
      onUploadProgress,
    })
    .then((res) => res.data);

export const downloadDocument = (id) =>
  api.get(`/documents/${id}/download/`, { responseType: "blob" });

export const archiveDocument = (id) => api.post(`/documents/${id}/archive/`);

export default api;