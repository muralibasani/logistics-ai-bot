import { useState, useRef, useEffect } from "react";
import "./App.css";
import { formatMessage } from "./utils/formatMessage";
import InsightsPanel from "./components/InsightsPanel";

interface Message {
  sender: "user" | "bot";
  text: string;
}

export default function App() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef<HTMLDivElement | null>(null);

  // Show welcome message on mount
  useEffect(() => {
    const welcomeMessage: Message = {
      sender: "bot",
      text: "Hello! 👋 Welcome to DL Logistics AI Assistant. I'm here to help you with order management.\n\nI can help you with:\n• Getting order details\n• Checking order status\n• Order counts and statistics\n• Canceling orders\n• Processing refunds\n\nHow can I assist you today?",
    };
    setMessages([welcomeMessage]);
  }, []);

  // auto scroll to bottom when new messages appear
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage: Message = { sender: "user", text: input };
    const questionText = input.trim(); // Capture the input before clearing
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch("http://localhost:8000/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: questionText }),
      });
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ detail: "Unknown error" }));
        throw new Error(errorData.detail || `HTTP error! status: ${res.status}`);
      }

      const data = await res.json();

      const botMessage: Message = { sender: "bot", text: data.answer };
      setMessages((prev) => [...prev, botMessage]);
    } catch (err) {
      console.error(err);
      const errorMessage = err instanceof Error ? err.message : "Something went wrong. Please try again.";
      setMessages((prev) => [
        ...prev,
        { sender: "bot", text: `⚠️ ${errorMessage}` },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <nav className="navbar">
        <div className="navbar-content">
          <h1 className="navbar-title">DL Logistics</h1>
        </div>
      </nav>

      <div className="main-content">
        <div className="insights-section">
          <InsightsPanel />
        </div>
        
        <div className="chat-container">
          <header className="chat-header">🤖 AI Assistant</header>

          <main className="chat-messages">
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`chat-bubble ${msg.sender === "user" ? "user" : "bot"}`}
              >
                {msg.sender === "bot" ? formatMessage(msg.text) : msg.text}
              </div>
            ))}
            {loading && <div className="chat-bubble bot">Thinking...</div>}
            <div ref={chatEndRef} />
          </main>

          <form className="chat-input-area" onSubmit={sendMessage}>
            <input
              type="text"
              style={{backgroundColor: "white", color : 'black'}}
              placeholder="Type your question..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={loading}
            />
            <button type="submit" disabled={loading}>
              {loading ? "..." : "Send"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
