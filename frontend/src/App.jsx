import { useEffect, useRef, useState } from "react";
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

  const [run, setRun] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [workflowLoading, setWorkflowLoading] = useState(false);
  const [workflowMessage, setWorkflowMessage] = useState("");
  const [workflowError, setWorkflowError] = useState("");

  const fileInputRef = useRef(null);
  const [checking, setChecking] = useState(true);

  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [uploadSuccess, setUploadSuccess] = useState(null);
  const [showUploadDialog, setShowUploadDialog] = useState(false);

  // Keep the created workflow available after upload.
  const [activeRun, setActiveRun] = useState(null);
  const [activeDocument, setActiveDocument] = useState(null);

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
    setWorkflowMessage("");
    setWorkflowError("");
    fileInputRef.current?.click();
  };

  const handleFileSelected = async (event) => {
    const file = event.target.files?.[0];

    if (!file) {
      return;
    }

    setSelectedFile(file);
    setWorkflowMessage("");
    setWorkflowError("");
    setWorkflowLoading(true);

    try {
      // 1. Create a processing run
      const runResponse = await fetch(`${API_URL}/runs`, {
        method: "POST",
      });

      if (!runResponse.ok) {
        throw new Error("Unable to create processing run.");
      }

      const createdRun = await runResponse.json();

      // 2. Upload the selected document
      const formData = new FormData();
      formData.append("file", file);

      const uploadResponse = await fetch(
        `${API_URL}/runs/${createdRun.id}/documents`,
        {
          method: "POST",
          body: formData,
        },
      );

      const uploadData = await uploadResponse.json().catch(() => null);

      if (!uploadResponse.ok) {
        throw new Error(uploadData?.detail || "Unable to upload document.");
      }

      setRun(createdRun);
      setWorkflowMessage(
        "Document uploaded successfully. It is ready to process.",
      );
    } catch (error) {
      setWorkflowError(error.message);
    } finally {
      setWorkflowLoading(false);

      // Allow selecting the same file again later.
      event.target.value = "";
    }
  };

  const handleProcess = async () => {
    if (!run) {
      return;
    }

    setWorkflowLoading(true);
    setWorkflowMessage("");
    setWorkflowError("");

    try {
      const response = await fetch(`${API_URL}/runs/${run.id}/process`, {
        method: "POST",
      });

      const data = await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(data?.detail || "Unable to process document.");
      }

      setRun(data);

      setWorkflowMessage(
        "Analysis complete. The document is ready for review.",
      );
    } catch (error) {
      setWorkflowError(error.message);
    } finally {
      setWorkflowLoading(false);
    }
  };

  const handleReview = async (action) => {
    if (!run) {
      return;
    }

    setWorkflowLoading(true);
    setWorkflowMessage("");
    setWorkflowError("");

    try {
      const response = await fetch(`${API_URL}/runs/${run.id}/${action}`, {
        method: "POST",
      });

      const data = await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(data?.detail || `Unable to ${action} the document.`);
      }

      setRun(data);

      setWorkflowMessage(
        action === "approve"
          ? "Document approved successfully."
          : "Document rejected.",
      );
    } catch (error) {
      setWorkflowError(error.message);
    } finally {
      setWorkflowLoading(false);
    }
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

      // Persist the active workflow in the frontend.
      setActiveRun(run);
      setActiveDocument(document);

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
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.txt,application/pdf,text/plain"
        onChange={handleFileSelected}
        style={{ display: "none" }}
      />

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

          {selectedFile && (
            <section className="workflow-panel">
              <div className="workflow-header">
                <div>
                  <span className="section-kicker">DOCUMENT WORKFLOW</span>

                  <h2>{selectedFile.name}</h2>

                  <p>
                    {Math.max(1, Math.round(selectedFile.size / 1024))} KB ·{" "}
                    {selectedFile.type === "application/pdf" ? "PDF" : "TXT"}
                  </p>
                </div>

                <div className="workflow-status">
                  <span className="status-dot" />

                  <span>{run?.status || "Preparing"}</span>
                </div>
              </div>

              <div className="workflow-details">
                <div>
                  <span>Run</span>
                  <strong>{run ? `${run.id.slice(0, 8)}…` : "Creating"}</strong>
                </div>

                <div>
                  <span>Stage</span>
                  <strong>{run?.current_stage || "ingest"}</strong>
                </div>

                <div>
                  <span>Review</span>
                  <strong>{run?.review_status || "Not required yet"}</strong>
                </div>
              </div>

              <div className="workflow-actions">
                {run?.status === "pending" && (
                  <button
                    type="button"
                    className="primary-action"
                    onClick={handleProcess}
                    disabled={workflowLoading}
                  >
                    {workflowLoading ? "Processing…" : "Process document"}
                  </button>
                )}

                {run?.status === "paused" &&
                  run?.current_stage === "review" && (
                    <>
                      <button
                        type="button"
                        className="primary-action"
                        onClick={() => handleReview("approve")}
                        disabled={workflowLoading}
                      >
                        {workflowLoading ? "Updating…" : "Approve"}
                      </button>

                      <button
                        type="button"
                        className="secondary-action"
                        onClick={() => handleReview("reject")}
                        disabled={workflowLoading}
                      >
                        Reject
                      </button>
                    </>
                  )}

                {run?.status === "completed" && (
                  <div className="workflow-complete">
                    Document successfully approved and completed.
                  </div>
                )}

                {run?.status === "failed" && (
                  <div className="workflow-failed">
                    Document processing was rejected or failed.
                  </div>
                )}
              </div>

              {workflowMessage && (
                <p className="workflow-message">{workflowMessage}</p>
              )}

              {workflowError && (
                <p className="workflow-error">{workflowError}</p>
              )}
            </section>
          )}

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

            <HealthCard
              label="Workflow"
              value={activeRun ? activeRun.status : "Ready"}
              status={activeRun ? "connected" : "connected"}
            />
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

            {activeRun && activeDocument ? (
              <div className="empty-activity">
                <div className="empty-icon">✓</div>

                <div>
                  <h3>{activeDocument.filename}</h3>
                  <p>Workflow created · Run {activeRun.id}</p>
                </div>
              </div>
            ) : (
              <EmptyActivity />
            )}
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

                  <div>
                    <span>Stage</span>
                    <strong>{uploadSuccess.run.current_stage}</strong>
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
