import axios from "axios";

export const CLIENT_SLUG = "acme-corp";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8000",
});

export async function uploadIngestion(kind, file, uploadedBy) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("client_slug", CLIENT_SLUG);
  formData.append("uploaded_by", uploadedBy);

  const response = await api.post(`/api/ingest/${kind}/`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
}

export async function fetchBatches() {
  const response = await api.get("/api/batches/", {
    params: { client_slug: CLIENT_SLUG },
  });
  return response.data;
}

export async function fetchRecords({ batchId, status, pageSize = 200 }) {
  if (!batchId) return { count: 0, results: [] };
  const response = await api.get("/api/records/", {
    params: {
      batch_id: batchId,
      status: status || undefined,
      page_size: pageSize,
    },
  });
  return response.data;
}

export async function fetchRecord(recordId) {
  const response = await api.get(`/api/records/${recordId}/`);
  return response.data;
}

export async function reviewRecord(recordId, payload) {
  const response = await api.patch(`/api/records/${recordId}/review/`, payload);
  return response.data;
}

export async function fetchAuditLog(recordId) {
  const response = await api.get(`/api/records/${recordId}/audit-log/`);
  return response.data;
}
