import { useState, useRef, useEffect } from "react";
import "./App.css";

function App() {
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState("company");
  const [logs, setLogs] = useState<string[]>([]);
  const [streaming, setStreaming] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setLogs([]);
    setStreaming(true);

    const url = `http://localhost:8000/api/v1/search/stream?query=${encodeURIComponent(
      query
    )}&mode=${mode}`;

    const source = new EventSource(url);
    eventSourceRef.current = source;

    source.onmessage = (event) => {
      setLogs((prev) => [...prev, event.data]);
    };

    source.onerror = () => {
      source.close();
      setStreaming(false);
    };
  };

  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

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

        <button type="submit" disabled={streaming}>
          {streaming ? "Running..." : "Run"}
        </button>
      </form>

      {logs.length > 0 && (
        <pre className="log-box">
          {logs.map((line, i) => (
            <div key={i}>{line}</div>
          ))}
        </pre>
      )}
    </div>
  );
}

export default App;
