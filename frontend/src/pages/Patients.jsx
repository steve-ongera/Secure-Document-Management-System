import { useEffect, useState } from "react";
import { getPatients } from "../services/api.js";

export default function Patients() {
  const [patients, setPatients] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadPatients = (params = {}) => {
    setLoading(true);
    getPatients(params)
      .then(setPatients)
      .catch(() => setError("Could not load patients."))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadPatients();
  }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    loadPatients(search ? { search } : {});
  };

  return (
    <div className="page">
      <h1>Patients</h1>

      <form className="search-bar" onSubmit={handleSearch}>
        <input
          type="text"
          placeholder="Search by name or National ID…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <button className="btn btn-primary" type="submit">
          Search
        </button>
      </form>

      {loading && <p>Loading…</p>}
      {error && <p className="text-error">{error}</p>}

      {!loading && !error && (
        <table className="table">
          <thead>
            <tr>
              <th>Name</th>
              <th>National ID</th>
              <th>Gender</th>
              <th>Date of Birth</th>
              <th>Documents</th>
            </tr>
          </thead>
          <tbody>
            {patients.map((p) => (
              <tr key={p.id}>
                <td>{p.full_name}</td>
                <td>{p.national_id}</td>
                <td>{p.gender}</td>
                <td>{p.date_of_birth}</td>
                <td>{p.document_count ?? 0}</td>
              </tr>
            ))}
            {patients.length === 0 && (
              <tr>
                <td colSpan="5">No patients found.</td>
              </tr>
            )}
          </tbody>
        </table>
      )}
    </div>
  );
}