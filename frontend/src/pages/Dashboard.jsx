import { useEffect, useState } from "react";
import { getDocuments, getPatients } from "../services/api.js";

export default function Dashboard() {
  const [stats, setStats] = useState({ patients: 0, documents: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([getPatients(), getDocuments()])
      .then(([patients, documents]) => {
        setStats({ patients: patients.length, documents: documents.length });
      })
      .catch(() => setError("Could not load dashboard data."))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="page">
      <h1>Dashboard</h1>
      {loading && <p>Loading…</p>}
      {error && <p className="text-error">{error}</p>}
      {!loading && !error && (
        <div className="card-grid">
          <div className="card">
            <p className="card-label">Total Patients</p>
            <p className="card-value">{stats.patients}</p>
          </div>
          <div className="card">
            <p className="card-label">Documents on File</p>
            <p className="card-value">{stats.documents}</p>
          </div>
        </div>
      )}
    </div>
  );
}