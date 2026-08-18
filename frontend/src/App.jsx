import { useEffect, useState } from "react";

const API_URL = "http://127.0.0.1:8000";

function App() {
  const [health, setHealth] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function checkHealth() {
      try {
        const response = await fetch(`${API_URL}/health`);

        if (!response.ok) {
          throw new Error(`Backend returned ${response.status}`);
        }

        const data = await response.json();
        setHealth(data);
      } catch (err) {
        setError(err.message);
      }
    }

    checkHealth();
  }, []);

  const connected = health?.status === "ok";

  return (
    <main className="app">
      <section className="card">
        <div className="eyebrow">DOCUMENT INTELLIGENCE PLATFORM</div>

        <h1>SuperDocs</h1>

        <p className="description">
          Agentic document analysis and workflow platform.
        </p>

        <div className="status-section">
          <h2>System Status</h2>

          {error ? (
            <div className="status error">
              <span className="indicator" />
              <div>
                <strong>Backend unavailable</strong>
                <p>{error}</p>
              </div>
            </div>
          ) : (
            <>
              <div className="status">
                <span className="indicator" />
                <div>
                  <strong>Backend</strong>
                  <p>{connected ? "Connected" : "Checking..."}</p>
                </div>
              </div>

              <div className="status">
                <span className="indicator" />
                <div>
                  <strong>Database</strong>
                  <p>
                    {health?.database === "connected"
                      ? "Connected"
                      : "Checking..."}
                  </p>
                </div>
              </div>
            </>
          )}
        </div>

        <div className="phase">
          <span>Current milestone</span>
          <strong>Phase 1 — Foundation</strong>
        </div>
      </section>
    </main>
  );
}

export default App;
