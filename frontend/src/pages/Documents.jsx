import { useEffect, useState } from "react";
import {
  archiveDocument,
  downloadDocument,
  getDocuments,
} from "../services/api.js";

const DOCUMENT_TYPES = [
  { value: "", label: "All types" },
  { value: "photo", label: "Patient Photo" },
  { value: "national_id", label: "National ID" },
  { value: "lab_report", label: "Lab Report" },
  { value: "xray", label: "X-Ray / Imaging" },
  { value: "prescription", label: "Prescription" },
  { value: "discharge_summary", label: "Discharge Summary" },
  { value: "insurance", label: "Insurance Document" },
  { value: "other", label: "Other" },
];

export default function Documents() {
  const [documents, setDocuments] = useState([]);
  const [filterType, setFilterType] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadDocuments = (params = {}) => {
    setLoading(true);
    getDocuments(params)
      .then(setDocuments)
      .catch(() => setError("Could not load documents."))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadDocuments();
  }, []);

  const handleFilter = (e) => {
    const value = e.target.value;
    setFilterType(value);
    loadDocuments(value ? { document_type: value } : {});
  };

  const handleDownload = async (doc) => {
    try {
      const res = await downloadDocument(doc.id);
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", doc.original_filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch {
      setError("Download failed.");
    }
  };

  const handleArchive = async (doc) => {
    if (!window.confirm(`Archive "${doc.original_filename}"?`)) return;
    await archiveDocument(doc.id);
    loadDocuments(filterType ? { document_type: filterType } : {});
  };

  return (
    <div className="page">
      <h1>Documents</h1>

      <div className="search-bar">
        <select value={filterType} onChange={handleFilter}>
          {DOCUMENT_TYPES.map((t) => (
            <option key={t.value} value={t.value}>
              {t.label}
            </option>
          ))}
        </select>
      </div>

      {loading && <p>Loading…</p>}
      {error && <p className="text-error">{error}</p>}

      {!loading && !error && (
        <table className="table">
          <thead>
            <tr>
              <th>Patient</th>
              <th>Type</th>
              <th>File</th>
              <th>Uploaded By</th>
              <th>Uploaded At</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {documents.map((doc) => (
              <tr key={doc.id}>
                <td>{doc.patient_name}</td>
                <td>{doc.document_type}</td>
                <td>{doc.original_filename}</td>
                <td>{doc.uploaded_by_display || "—"}</td>
                <td>{new Date(doc.uploaded_at).toLocaleString()}</td>
                <td className="actions">
                  <button
                    className="btn btn-ghost"
                    onClick={() => handleDownload(doc)}
                  >
                    Download
                  </button>
                  <button
                    className="btn btn-ghost text-error"
                    onClick={() => handleArchive(doc)}
                  >
                    Archive
                  </button>
                </td>
              </tr>
            ))}
            {documents.length === 0 && (
              <tr>
                <td colSpan="6">No documents found.</td>
              </tr>
            )}
          </tbody>
        </table>
      )}
    </div>
  );
}