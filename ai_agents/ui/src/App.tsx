import { useState, useRef, useEffect } from "react";
import axios from "axios";
import "./App.css";

function App() {
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState("company");
  const [logs, setLogs] = useState<string[]>([]);
  const [streaming, setStreaming] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);
  const [orchestratedConfig, setOrchestratedConfig] = useState({
    openai_api_key: "",
    data_source: { 
    type: "csv",
    file_path: "ai_agents/data/company_names.csv"
  },
  browser_timeout: "30",
  max_companies: "3",
  parallel_processing: "false",
  search_query: "",
  target_executives: "Founder/CEO"
  });
  const [configStatus, setConfigStatus] = useState("");
  const handleConfigChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    if (name === "file_path") {
      setOrchestratedConfig(prev => ({
        ...prev,
        data_source: {
          ...prev.data_source,
          file_path: value
        }
      }));
    } else if (name === "search_query" || name === "target_executives") {
    setOrchestratedConfig(prev => ({
      ...prev,
      [name]: value
    }));
  } else {
      setOrchestratedConfig(prev => ({ ...prev, [name]: value }));
    }
  };  
  const handleOrchestratedSubmit = async () => {
    setIsRunning(true);
  setConfigStatus("Running orchestrated workflow...");


  try {
    const response = await axios.post("http://localhost:8000/api/v1/orchestrated/run", {
      config: {
        openai_api_key: orchestratedConfig.openai_api_key,
        query,
        search_query:query,
        target_executives: orchestratedConfig.target_executives,
        data_source: orchestratedConfig.data_source,
        browser_timeout: parseInt(orchestratedConfig.browser_timeout),
        max_companies: parseInt(orchestratedConfig.max_companies),
        parallel_processing: orchestratedConfig.parallel_processing === "true"
      }
    });

    if (response.data.status === "success") {
      setConfigStatus("✅ Workflow started successfully.");
    } else {
      setConfigStatus(`❌ Error: ${response.data.message}`);
    }
  } catch (error: any) {
    if (error.response?.data?.message) {
      setConfigStatus(`❌ Error: ${error.response.data.message}`);
    } else {
      setConfigStatus("❌ Request failed.");
      console.error(error);
    }
  }
  finally {
    setIsRunning(false);
  }
};
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

  const handleEnhance = async () => {
    try {
      const response = await axios.post("http://localhost:8000/api/v1/enhance", {
        query,
      });

      if (response.data.enhanced) {
        console.log("Enhanced query:", response.data.enhanced);
        setQuery(response.data.enhanced);
      }
    } catch (error) {
      console.error("Enhance failed:", error);
    }
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

    <div className="orchestrated-config">
      <form onSubmit={handleSubmit}>
        <div className="query-row">
          <input
            type="text"
            placeholder="Enter your query"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            required
            className="query-input"
          />
          <button type="button" onClick={handleEnhance} className="enhance-button">
            ✨ Enhance
          </button>
        </div>
      </form>
    <textarea
      name="target_executives"
      placeholder="Enter target executive roles (e.g., Founder, CEO, Head of Marketing)"
      value={orchestratedConfig.target_executives || ""}
      onChange={handleConfigChange}
      rows={3}
    />
  <button type="button" onClick={handleOrchestratedSubmit} disabled={isRunning}>
    {!isRunning ? "Run Orchestrated Workflow" : "Running"}
  </button>
  {configStatus && <p>{configStatus}</p>}
</div>


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
