
import { useState, useEffect } from "react";
import axios from "axios";
import "./App.css";

// Use the configured backend URL, or default to localhost.
const API_URL =
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

function App() {
  const [documents, setDocuments] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [selectedDocument, setSelectedDocument] = useState("");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState([]);
  const [chatHistory, setChatHistory] = useState([]);

  const [uploading, setUploading] = useState(false);
  const [asking, setAsking] = useState(false);
  const [error, setError] = useState("");

  // Fetch uploaded documents
  const fetchDocuments = async () => {
    try {
      const response = await axios.get(`${API_URL}/documents`);
      setDocuments(response.data.documents);
      setError("");
    } catch (error) {
      console.error("Failed to fetch documents:", error);
      setError("Could not load documents. Is the backend running?");
    }
  };

  // Load documents when application starts
  useEffect(() => {
    fetchDocuments();
  }, []);

  // Upload PDF
  const uploadPDF = async () => {
    if (!selectedFile) {
      alert("Please select a PDF first.");
      return;
    }

    if (
      selectedFile.type !== "application/pdf" &&
      !selectedFile.name.toLowerCase().endsWith(".pdf")
    ) {
      alert("Please select a valid PDF file.");
      return;
    }

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      setUploading(true);
      setError("");

      const response = await axios.post(
        `${API_URL}/upload`,
        formData
      );

      alert(response.data.message);
      setSelectedFile(null);
      await fetchDocuments();
    } catch (error) {
      console.error("Upload failed:", error);
      setError(
        error.response?.data?.detail ||
        "PDF upload failed. Check the backend terminal."
      );
    } finally {
      setUploading(false);
    }
  };

  // Ask a question using RAG
  const askQuestion = async () => {
    if (!question.trim()) {
      alert("Please enter a question.");
      return;
    }

    const currentQuestion = question.trim();

    try {
      setAsking(true);
      setAnswer("");
      setSources([]);
      setError("");

      const response = await axios.post(`${API_URL}/ask`, {
        question: currentQuestion,
        filename: selectedDocument || null
      });

      const newAnswer = response.data.answer;
      const newSources = response.data.sources || [];

      setAnswer(newAnswer);
      setSources(newSources);

      setChatHistory((previous) => [
        ...previous,
        {
          question: currentQuestion,
          answer: newAnswer,
          sources: newSources
        }
      ]);

      setQuestion("");
    } catch (error) {
      console.error("Question failed:", error);
      setError(
        error.response?.data?.detail ||
        "Failed to generate an answer. Please try again."
      );
    } finally {
      setAsking(false);
    }
  };

  return (
    <div className="app">
      <h1>Document Q&A Assistant</h1>
      <p>Upload PDFs and ask questions using AI.</p>

      {/* PDF Upload Section */}
      <div className="upload-section">
        <h2>Upload a PDF</h2>

        <input
          type="file"
          accept=".pdf,application/pdf"
          onChange={(e) =>
            setSelectedFile(e.target.files?.[0] || null)
          }
        />

        {selectedFile && (
          <p>Selected: {selectedFile.name}</p>
        )}

        <button
          onClick={uploadPDF}
          disabled={uploading || !selectedFile}
        >
          {uploading ? "Processing PDF..." : "Upload PDF"}
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="error-message">{error}</div>
      )}

      {/* Uploaded Documents */}
      <div className="documents-section">
        <h2>Uploaded Documents</h2>

        {documents.length === 0 ? (
          <p>No documents uploaded yet.</p>
        ) : (
          <>
            <select
              value={selectedDocument}
              onChange={(e) => setSelectedDocument(e.target.value)}
            >
              <option value="">Search all documents</option>

              {documents.map((doc) => (
                <option key={doc.filename} value={doc.filename}>
                  {doc.filename} ({doc.chunks} chunks)
                </option>
              ))}
            </select>

            {documents.map((doc) => (
              <div className="document-item" key={doc.filename}>
                <span>📄 {doc.filename}</span>
                <span>{doc.chunks} chunks</span>
              </div>
            ))}
          </>
        )}

        <button onClick={fetchDocuments}>
          Refresh Documents
        </button>
      </div>

      {/* Chat Section */}
      <div className="chat-section">
        <h2>Ask Your Documents</h2>

        <p>
          {selectedDocument
            ? `Currently searching: ${selectedDocument}`
            : "Currently searching across all documents"}
        </p>

        <textarea
          placeholder="Ask something about your documents..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          rows={4}
        />

        <button
          onClick={askQuestion}
          disabled={asking || !question.trim()}
        >
          {asking ? "Generating answer..." : "Ask Gemini"}
        </button>

        {/* Current Answer */}
        {answer && (
          <div className="answer-section">
            <h3>Latest Answer</h3>
            <p>{answer}</p>

            {sources.length > 0 && (
              <div className="sources-section">
                <h4>Sources</h4>

                {sources.map((source, index) => (
                  <div
                    className="source-item"
                    key={`${source.filename}-${source.page}-${index}`}
                  >
                    📄 {source.filename} — Page {source.page}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Chat History */}
        {chatHistory.length > 0 && (
          <div className="chat-history">
            <h3>Conversation History</h3>

            {chatHistory.map((chat, index) => (
              <div className="chat-message" key={index}>
                <div className="user-message">
                  <strong>You</strong>
                  <p>{chat.question}</p>
                </div>

                <div className="ai-message">
                  <strong>Gemini</strong>
                  <p>{chat.answer}</p>

                  {chat.sources.length > 0 && (
                    <div className="sources-section">
                      <h4>Sources</h4>

                      {chat.sources.map((source, sourceIndex) => (
                        <div
                          className="source-item"
                          key={`${source.filename}-${source.page}-${sourceIndex}`}
                        >
                          📄 {source.filename} — Page {source.page}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
