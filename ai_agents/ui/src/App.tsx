import { useState, useRef, useEffect } from "react";
import axios from "axios";
import "./App.css";

function App() {
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState("company");
  const [logs, setLogs] = useState<string[]>([]);
  const [streaming, setStreaming] = useState(false);
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
  setConfigStatus("Running orchestrated workflow...");

  if (!orchestratedConfig.openai_api_key) {
    setConfigStatus("❌ Error: OpenAI API key is required");
    return;
  }

  try {
    const response = await axios.post("http://localhost:8000/api/v1/orchestrated/run", {
      config: {
        openai_api_key: orchestratedConfig.openai_api_key,
        search_query: orchestratedConfig.search_query,
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

        <select value={mode} onChange={(e) => setMode(e.target.value)}>
          <option value="company">Company only</option>
          <option value="company-employee">Company + Employee</option>
        </select>

        <button type="submit" disabled={streaming}>
          {streaming ? "Running..." : "Run"}
        </button>
      </form>
      <h2>Run Orchestrated SDR</h2>
  <div className="orchestrated-config">
  <input
    name="openai_api_key"
    placeholder="OpenAI API Key"
    value={orchestratedConfig.openai_api_key}
    onChange={handleConfigChange}
  />
  <input
    name="data_source.file_path" 
    placeholder="CSV File Path"
    value={orchestratedConfig.data_source.file_path}
    onChange={(e) => setOrchestratedConfig(prev => ({
      ...prev,
      data_source: {
        ...prev.data_source,
        file_path: e.target.value
      }
    }))}
  />
  <input
    name="browser_timeout"
    type="number" 
    placeholder="Browser Timeout"
    value={orchestratedConfig.browser_timeout}
    onChange={handleConfigChange}
  />
  <input
    name="max_companies"
    type="number" 
    placeholder="Max Companies"
    value={orchestratedConfig.max_companies}
    onChange={handleConfigChange}
  />
  <textarea
          name="search_query"
          placeholder="Enter your search query (e.g., 'Find 1 company in Dubai that sells electronics')"
          value={orchestratedConfig.search_query}
          onChange={handleConfigChange}
          rows={3}
        />
    <textarea
      name="target_executives"
      placeholder="Enter target executive roles (e.g., Founder, CEO, Head of Marketing)"
      value={orchestratedConfig.target_executives || ""}
      onChange={handleConfigChange}
      rows={3}
    />
  <select 
    name="parallel_processing" 
    value={orchestratedConfig.parallel_processing.toString()} 
    onChange={handleConfigChange}
  >
    <option value="false">Sequential</option>
    <option value="true">Parallel</option>
  </select>
  <button type="button" onClick={handleOrchestratedSubmit}>
    Run Orchestrated Workflow
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
