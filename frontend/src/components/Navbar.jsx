import { useNavigate } from "react-router-dom";
import { logout } from "../services/api.js";

export default function Navbar() {
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <header className="navbar">
      <div className="navbar-brand">
        <span className="navbar-logo">A1</span>
        <span>Afya1 HMIS — Documents</span>
      </div>
      <div className="navbar-actions">
        <button className="btn btn-ghost" onClick={handleLogout}>
          Log out
        </button>
      </div>
    </header>
  );
}