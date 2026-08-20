import { useEffect, useState } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

function StatusDot({ status }) {
  return <span className={`status-dot ${status}`} aria-hidden="true" />;
}

function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">S</div>

        <div>
          <div className="brand-name">SuperDocs</div>
          <div className="brand-subtitle">Document intelligence</div>
        </div>
      </div>

      <nav className="navigation" aria-label="Main navigation">
        <div className="nav-section-label">Workspace</div>

        <button className="nav-item active" type="button">
          <span className="nav-icon">⌂</span>
          <span>Overview</span>
        </button>

        <button className="nav-item" type="button">
          <span className="nav-icon">▤</span>
          <span>Documents</span>
        </button>

        <button className="nav-item" type="button">
          <span className="nav-icon">◷</span>
          <span>Runs</span>
        </button>

        <div className="nav-section-label nav-section-spaced">Manage</div>

        <button className="nav-item" type="button">
          <span className="nav-icon">⚙</span>
          <span>Settings</span>
        </button>
      </nav>

      <div className="sidebar-footer">
        <div className="connection-card">
          <div className="connection-header">
            <span>System</span>
            <StatusDot status="checking" />
          </div>
          <span className="connection-text">Checking connection</span>
        </div>

        <div className="profile">
          <div className="avatar">A</div>
          <div className="profile-copy">
            <strong>Workspace</strong>
            <span>SuperDocs</span>
          </div>
          <span className="profile-menu">•••</span>
        </div>
      </div>
    </aside>
  );
}

function Header({ onUpload }) {
  return (
    <header className="topbar">
      <div className="mobile-brand">
        <div className="brand-mark small">S</div>
        <span>SuperDocs</span>
      </div>

      <div className="topbar-actions">
        <button
          className="icon-button"
          type="button"
          aria-label="Notifications"
        >
          ♢
        </button>

        <button className="primary-button" type="button" onClick={onUpload}>
          <span>+</span>
          Upload document
        </button>
      </div>
    </header>
  );
}

function HealthCard({ label, value, status, error }) {
  return (
    <div className="health-card">
      <div className="health-card-top">
        <span>{label}</span>
        <StatusDot status={status} />
      </div>

      <strong>{value}</strong>

      {error && <p>{error}</p>}
    </div>
  );
}

function EmptyActivity() {
  return (
    <div className="empty-activity">
      <div className="empty-icon">✦</div>

      <div>
        <h3>No recent activity</h3>
        <p>Upload your first document to start an analysis workflow.</p>
      </div>
    </div>
  );
}

function App() {
  const [health, setHealth] = useState(null);
  const [error, setError] = useState(null);
  const [checking, setChecking] = useState(true);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [uploadSuccess, setUploadSuccess] = useState(null);
  const [showUploadDialog, setShowUploadDialog] = useState(false);

  useEffect(() => {
    async function checkHealth() {
      try {
        setChecking(true);

        const response = await fetch(`${API_URL}/health`);

        if (!response.ok) {
          throw new Error(`Backend returned ${response.status}`);
        }

        const data = await response.json();

        setHealth(data);
        setError(null);
      } catch (err) {
        setHealth(null);
        setError(err.message);
      } finally {
        setChecking(false);
      }
    }

    checkHealth();
  }, []);

  const backendConnected = health?.status === "ok";
  const databaseConnected = health?.database === "connected";

  const handleUpload = () => {
    setUploadError(null);
    setUploadSuccess(null);
    setSelectedFile(null);
    setShowUploadDialog(true);
  };

  const handleFileChange = (event) => {
    const file = event.target.files?.[0];

    if (!file) {
      return;
    }

    const allowedTypes = ["application/pdf", "text/plain"];

    if (!allowedTypes.includes(file.type)) {
      setUploadError("Please choose a PDF or TXT file.");
      setSelectedFile(null);
      return;
    }

    if (file.size === 0) {
      setUploadError("The selected file is empty.");
      setSelectedFile(null);
      return;
    }

    setUploadError(null);
    setUploadSuccess(null);
    setSelectedFile(file);
  };

  const submitUpload = async () => {
    if (!selectedFile) {
      setUploadError("Choose a document first.");
      return;
    }

    try {
      setUploading(true);
      setUploadError(null);
      setUploadSuccess(null);

      // 1. Create a run.
      const runResponse = await fetch(`${API_URL}/runs`, {
        method: "POST",
      });

      if (!runResponse.ok) {
        throw new Error(`Unable to create run (${runResponse.status})`);
      }

      const run = await runResponse.json();

      // 2. Attach the document to the run.
      const formData = new FormData();
      formData.append("file", selectedFile);

      const documentResponse = await fetch(
        `${API_URL}/runs/${run.id}/documents`,
        {
          method: "POST",
          body: formData,
        },
      );

      if (!documentResponse.ok) {
        let message = `Upload failed (${documentResponse.status})`;

        try {
          const errorData = await documentResponse.json();
          if (errorData.detail) {
            message = errorData.detail;
          }
        } catch {
          // Keep the default error message.
        }

        throw new Error(message);
      }

      const document = await documentResponse.json();

      setUploadSuccess({
        run,
        document,
      });

      setSelectedFile(null);
    } catch (err) {
      setUploadError(err.message);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="app-shell">
      <Sidebar />

      <div className="main-area">
        <Header onUpload={handleUpload} />

        <main className="workspace">
          <section className="welcome-section">
            <div>
              <div className="eyebrow">DOCUMENT INTELLIGENCE PLATFORM</div>

              <h1>Good morning.</h1>

              <p>Turn documents into structured insights with SuperDocs.</p>
            </div>

            <button className="secondary-button" type="button">
              View documentation
              <span>↗</span>
            </button>
          </section>

          <section className="hero-panel">
            <div className="hero-content">
              <div className="hero-badge">
                <span className="spark">✦</span>
                Agentic document workflow
              </div>

              <h2>
                From document to
                <br />
                <span>useful insight.</span>
              </h2>

              <p>
                Upload a document and let SuperDocs extract, analyze, and
                prepare the information you need.
              </p>

              <button
                className="hero-button"
                type="button"
                onClick={handleUpload}
              >
                <span className="upload-symbol">↑</span>
                Upload your first document
              </button>
            </div>

            <div className="hero-visual" aria-hidden="true">
              <div className="document-stack">
                <div className="document-back" />
                <div className="document-middle" />

                <div className="document-front">
                  <div className="document-top-line" />
                  <div className="document-title-line" />
                  <div className="document-line long" />
                  <div className="document-line medium" />
                  <div className="document-line short" />

                  <div className="document-analysis">
                    <span>AI analysis</span>
                    <div className="analysis-bars">
                      <i />
                      <i />
                      <i />
                    </div>
                  </div>
                </div>

                <div className="floating-chip chip-one">
                  <span>✓</span>
                  Extracted
                </div>

                <div className="floating-chip chip-two">
                  <span>✦</span>
                  Analyzing
                </div>
              </div>
            </div>
          </section>

          <section className="section-heading">
            <div>
              <h2>System overview</h2>
              <p>Everything is ready when you are.</p>
            </div>
          </section>

          <section className="health-grid">
            <HealthCard
              label="Backend"
              value={
                checking
                  ? "Checking..."
                  : backendConnected
                    ? "Connected"
                    : "Unavailable"
              }
              status={
                checking ? "checking" : backendConnected ? "connected" : "error"
              }
              error={!checking && error ? error : null}
            />

            <HealthCard
              label="Database"
              value={
                checking
                  ? "Checking..."
                  : databaseConnected
                    ? "Connected"
                    : "Unavailable"
              }
              status={
                checking
                  ? "checking"
                  : databaseConnected
                    ? "connected"
                    : "error"
              }
            />

            <HealthCard label="Workflow" value="Ready" status="connected" />
          </section>

          <section className="activity-section">
            <div className="section-heading">
              <div>
                <h2>Recent activity</h2>
                <p>Your latest document workflows will appear here.</p>
              </div>

              <button className="text-button" type="button">
                View all
                <span>→</span>
              </button>
            </div>

            <EmptyActivity />
          </section>
        </main>
      </div>

      {showUploadDialog && (
        <div className="upload-overlay">
          <div className="upload-dialog">
            <div className="upload-dialog-header">
              <div>
                <div className="eyebrow">NEW WORKFLOW</div>
                <h2>Upload a document</h2>
                <p>
                  Choose a PDF or text document to start a new analysis
                  workflow.
                </p>
              </div>

              <button
                className="dialog-close"
                type="button"
                onClick={() => setShowUploadDialog(false)}
                disabled={uploading}
                aria-label="Close upload dialog"
              >
                ×
              </button>
            </div>

            {!uploadSuccess ? (
              <>
                <label className="upload-dropzone">
                  <input
                    type="file"
                    accept=".pdf,.txt,application/pdf,text/plain"
                    onChange={handleFileChange}
                    disabled={uploading}
                  />

                  <span className="upload-dropzone-icon">↑</span>

                  <strong>
                    {selectedFile ? selectedFile.name : "Choose a document"}
                  </strong>

                  <span>
                    {selectedFile
                      ? `${(selectedFile.size / 1024).toFixed(1)} KB`
                      : "PDF or TXT files"}
                  </span>
                </label>

                {uploadError && (
                  <div className="upload-error">{uploadError}</div>
                )}

                <div className="upload-dialog-actions">
                  <button
                    className="secondary-button"
                    type="button"
                    onClick={() => setShowUploadDialog(false)}
                    disabled={uploading}
                  >
                    Cancel
                  </button>

                  <button
                    className="primary-button"
                    type="button"
                    onClick={submitUpload}
                    disabled={!selectedFile || uploading}
                  >
                    {uploading ? "Uploading..." : "Start analysis"}
                  </button>
                </div>
              </>
            ) : (
              <div className="upload-success">
                <div className="success-icon">✓</div>

                <h3>Document uploaded</h3>

                <p>
                  <strong>{uploadSuccess.document.filename}</strong> has been
                  added to a new workflow.
                </p>

                <div className="upload-result">
                  <div>
                    <span>Run</span>
                    <strong>{uploadSuccess.run.id}</strong>
                  </div>

                  <div>
                    <span>Status</span>
                    <strong>{uploadSuccess.run.status}</strong>
                  </div>
                </div>

                <button
                  className="primary-button"
                  type="button"
                  onClick={() => setShowUploadDialog(false)}
                >
                  Done
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
