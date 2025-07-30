import { useState } from "react";
import axios from "axios";
import "./App.css";

function App() {
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState("company");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setSuccess(false);
    setError("");

    try {
      const res = await axios.post("http://localhost:8000/api/v1/search", {
        query,
        mode,
      });

      if (res.data.status === "success") {
        setSuccess(true);
      } else {
        setError(res.data.message || "Unknown error.");
      }
    } catch (err) {
      setError("Failed to connect to backend.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <h1>Agent Hub</h1>

      <form onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Enter your query"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          required
        />

        <select value={mode} onChange={(e) => setMode(e.target.value)}>
          <option value="company">Company only</option>
          <option value="company-employee">Company + Employee</option>
        </select>

        <button type="submit" disabled={loading}>
          {loading ? "Running..." : "Run"}
        </button>
      </form>

      {success && <p className="success">✅ Done.</p>}
      {error && <p className="error">{error}</p>}
    </div>
  );
}

export default App;
