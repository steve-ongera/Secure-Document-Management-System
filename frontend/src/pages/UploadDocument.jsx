import { useEffect, useState } from "react";
import { getPatients, uploadDocument } from "../services/api.js";

const DOCUMENT_TYPES = [
  "photo",
  "national_id",
  "lab_report",
  "xray",
  "prescription",
  "discharge_summary",
  "insurance",
  "other",
];

const ALLOWED_TYPES = ["image/jpeg", "image/png", "application/pdf"];
const MAX_SIZE_MB = 10;

export default function UploadDocument() {
  const [patients, setPatients] = useState([]);
  const [patientId, setPatientId] = useState("");
  const [documentType, setDocumentType] = useState(DOCUMENT_TYPES[0]);
  const [description, setDescription] = useState("");
  const [file, setFile] = useState(null);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState({ type: "", message: "" });

  useEffect(() => {
    getPatients().then(setPatients).catch(() => {});
  }, []);

  const validateFile = (selected) => {
    if (!ALLOWED_TYPES.includes(selected.type)) {
      return "Only JPEG, PNG, or PDF files are allowed.";
    }
    if (selected.size > MAX_SIZE_MB * 1024 * 1024) {
      return `File must be smaller than ${MAX_SIZE_MB}MB.`;
    }
    return null;
  };

  const handleFileChange = (e) => {
    const selected = e.target.files[0];
    if (!selected) return;
    const error = validateFile(selected);
    if (error) {
      setStatus({ type: "error", message: error });
      setFile(null);
      return;
    }
    setStatus({ type: "", message: "" });
    setFile(selected);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!patientId || !file) {
      setStatus({ type: "error", message: "Select a patient and a file." });
      return;
    }

    const formData = new FormData();
    formData.append("patient", patientId);
    formData.append("document_type", documentType);
    formData.append("description", description);
    formData.append("file", file);

    try {
      setStatus({ type: "", message: "" });
      await uploadDocument(formData, (evt) => {
        setProgress(Math.round((evt.loaded * 100) / evt.total));
      });
      setStatus({ type: "success", message: "Document uploaded successfully." });
      setFile(null);
      setDescription("");
      setProgress(0);
    } catch (err) {
      const apiError =
        err.response?.data?.file?.[0] ||
        err.response?.data?.detail ||
        "Upload failed. Please try again.";
      setStatus({ type: "error", message: apiError });
      setProgress(0);
    }
  };

  return (
    <div className="page">
      <h1>Upload Document</h1>

      <form className="form" onSubmit={handleSubmit}>
        <label>
          Patient
          <select
            value={patientId}
            onChange={(e) => setPatientId(e.target.value)}
            required
          >
            <option value="">Select patient…</option>
            {patients.map((p) => (
              <option key={p.id} value={p.id}>
                {p.full_name} — {p.national_id}
              </option>
            ))}
          </select>
        </label>

        <label>
          Document Type
          <select
            value={documentType}
            onChange={(e) => setDocumentType(e.target.value)}
          >
            {DOCUMENT_TYPES.map((t) => (
              <option key={t} value={t}>
                {t.replace(/_/g, " ")}
              </option>
            ))}
          </select>
        </label>

        <label>
          Description (optional)
          <input
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="e.g. Chest X-ray, follow-up visit"
          />
        </label>

        <label>
          File (JPEG, PNG, or PDF — max {MAX_SIZE_MB}MB)
          <input
            type="file"
            accept=".jpg,.jpeg,.png,.pdf"
            onChange={handleFileChange}
            required
          />
        </label>

        {progress > 0 && progress < 100 && (
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${progress}%` }} />
          </div>
        )}

        {status.message && (
          <p className={status.type === "error" ? "text-error" : "text-success"}>
            {status.message}
          </p>
        )}

        <button className="btn btn-primary" type="submit">
          Upload
        </button>
      </form>
    </div>
  );
}