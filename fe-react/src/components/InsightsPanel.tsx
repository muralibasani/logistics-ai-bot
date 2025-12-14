import { useState, useEffect } from "react";
import "./InsightsPanel.css";

interface Insight {
  insight_id: string;
  insight_type: string;
  title: string;
  description: string;
  data: Record<string, string>;
  priority: "low" | "medium" | "high";
  timestamp: string;
}

interface InsightsResponse {
  insights: Insight[];
  count: number;
}

export default function InsightsPanel() {
  const [insights, setInsights] = useState<Insight[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedInsight, setExpandedInsight] = useState<string | null>(null);
  const [filterPriority, setFilterPriority] = useState<"all" | "high" | "medium" | "low">("all");

  const fetchInsights = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch("http://localhost:8000/insights");
      if (!response.ok) {
        throw new Error(`Failed to fetch insights: ${response.statusText}`);
      }
      const data: InsightsResponse = await response.json();
      setInsights(data.insights);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load insights");
      console.error("Error fetching insights:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInsights();
    // Refresh insights every 5 minutes
    const interval = setInterval(fetchInsights, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const getPriorityClass = (priority: string) => {
    switch (priority) {
      case "high":
        return "priority-high";
      case "medium":
        return "priority-medium";
      case "low":
        return "priority-low";
      default:
        return "";
    }
  };

  const formatData = (data: Record<string, string>) => {
    return Object.entries(data).map(([key, value]) => (
      <div key={key} className="insight-data-item">
        <strong>{key.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}:</strong>{" "}
        <span>{value}</span>
      </div>
    ));
  };

  const toggleExpand = (insightId: string) => {
    setExpandedInsight(expandedInsight === insightId ? null : insightId);
  };

  const filteredInsights = filterPriority === "all" 
    ? insights 
    : insights.filter(insight => insight.priority === filterPriority);

  const handlePriorityFilter = (priority: "all" | "high" | "medium" | "low") => {
    setFilterPriority(priority);
    setExpandedInsight(null); // Collapse all when filtering
  };

  return (
    <div className="insights-panel">
      <div className="insights-header">
        <h2>📊 Business Insights</h2>
        <button onClick={fetchInsights} disabled={loading} className="refresh-button">
          {loading ? "Loading..." : "🔄 Refresh"}
        </button>
      </div>

      {/* Priority Filter */}
      {insights.length > 0 && (
        <div className="insights-filters">
          <span className="filter-label">Filter:</span>
          <button
            className={`filter-button ${filterPriority === "all" ? "active" : ""}`}
            onClick={() => handlePriorityFilter("all")}
          >
            All ({insights.length})
          </button>
          <button
            className={`filter-button priority-high ${filterPriority === "high" ? "active" : ""}`}
            onClick={() => handlePriorityFilter("high")}
          >
            High ({insights.filter(i => i.priority === "high").length})
          </button>
          <button
            className={`filter-button priority-medium ${filterPriority === "medium" ? "active" : ""}`}
            onClick={() => handlePriorityFilter("medium")}
          >
            Medium ({insights.filter(i => i.priority === "medium").length})
          </button>
          <button
            className={`filter-button priority-low ${filterPriority === "low" ? "active" : ""}`}
            onClick={() => handlePriorityFilter("low")}
          >
            Low ({insights.filter(i => i.priority === "low").length})
          </button>
        </div>
      )}

      {error && (
        <div className="insights-error">
          ⚠️ {error}
        </div>
      )}

      {loading && insights.length === 0 ? (
        <div className="insights-loading">Loading insights...</div>
      ) : filteredInsights.length === 0 ? (
        <div className="insights-empty">
          {filterPriority !== "all" 
            ? `No ${filterPriority} priority insights available.` 
            : "No insights available at this time."}
        </div>
      ) : (
        <div className="insights-list">
          {filteredInsights.map((insight) => {
            const isExpanded = expandedInsight === insight.insight_id;
            return (
              <div
                key={insight.insight_id}
                className={`insight-card ${getPriorityClass(insight.priority)} ${isExpanded ? "expanded" : ""}`}
                onClick={() => toggleExpand(insight.insight_id)}
              >
                <div className="insight-header">
                  <div className="insight-header-content">
                    <h3 className="insight-title">{insight.title}</h3>
                    <span className={`priority-badge ${getPriorityClass(insight.priority)}`}>
                      {insight.priority}
                    </span>
                  </div>
                  <button className="expand-button" aria-label="Toggle expand">
                    {isExpanded ? "▼" : "▶"}
                  </button>
                </div>
                <p className="insight-description">{insight.description}</p>
                {isExpanded && (
                  <div className="insight-data-expanded">
                    {formatData(insight.data)}
                    <div className="insight-timestamp">
                      Generated: {new Date(insight.timestamp).toLocaleString()}
                    </div>
                  </div>
                )}
                {!isExpanded && (
                  <div className="insight-data-preview">
                    {Object.entries(insight.data).slice(0, 2).map(([key, value]) => (
                      <div key={key} className="insight-data-item-preview">
                        <strong>{key.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}:</strong>{" "}
                        <span>{value}</span>
                      </div>
                    ))}
                    {Object.keys(insight.data).length > 2 && (
                      <div className="insight-more-indicator">Click to see more...</div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

