import { useMemo, useState } from 'react';

function entrySeverity(entry) {
  return String(entry.analysis?.triage?.severity || 'Unknown')
    .trim()
    .toLowerCase();
}

function severityLabel(value) {
  return value === 'unknown' ? 'Unknown' : value.charAt(0).toUpperCase() + value.slice(1);
}

export default function HistoryView({ entries, onOpen, onDelete }) {
  const [query, setQuery] = useState('');
  const [severity, setSeverity] = useState('all');
  const normalizedQuery = query.trim().toLowerCase();
  const filteredEntries = useMemo(
    () =>
      entries.filter((entry) => {
        const searchable = [entry.id, entry.analysis?.bug_id, entry.title, entry.bugReport]
          .filter(Boolean)
          .join(' ')
          .toLowerCase();
        const matchesQuery = !normalizedQuery || searchable.includes(normalizedQuery);
        const matchesSeverity = severity === 'all' || entrySeverity(entry) === severity;
        return matchesQuery && matchesSeverity;
      }),
    [entries, normalizedQuery, severity],
  );
  const severityCounts = ['critical', 'high', 'medium', 'low'].map((value) => ({
    value,
    count: entries.filter((entry) => entrySeverity(entry) === value).length,
  }));

  return (
    <section className="page-panel panel" id="history">
      <div className="page-heading">
        <div>
          <p className="eyebrow">WORKSPACE</p>
          <h2>Analysis History</h2>
        </div>
        <span className="count-pill">
          {filteredEntries.length === entries.length
            ? `${entries.length} saved`
            : `${filteredEntries.length} shown`}
        </span>
      </div>
      <div className="history-toolbar">
        <label className="history-search">
          <span>⌕</span>
          <input
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search by bug ID, title, error, file..."
            aria-label="Search analysis history"
          />
        </label>
        <label className="history-filter">
          <span>Filter by Severity</span>
          <select
            value={severity}
            onChange={(event) => setSeverity(event.target.value)}
            aria-label="Filter history by severity"
          >
            <option value="all">All Severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </label>
      </div>
      <div className="history-stats">
        <div className="history-stat all">
          <i>▧</i>
          <span>All Severities</span>
          <b>{entries.length}</b>
          <small>Total Analyses</small>
        </div>
        {severityCounts.map((item) => (
          <div className={`history-stat ${item.value}`} key={item.value}>
            <i>●</i>
            <span>{severityLabel(item.value)}</span>
            <b>{item.count}</b>
            <small>Analyses</small>
          </div>
        ))}
      </div>
      {entries.length === 0 ? (
        <div className="empty-state">
          <span>◷</span>
          <h3>No analyses yet</h3>
          <p>Completed bug analyses will appear here.</p>
        </div>
      ) : filteredEntries.length === 0 ? (
        <div className="empty-state">
          <span>⌕</span>
          <h3>No matching analyses</h3>
          <p>Try a different search term or severity filter.</p>
        </div>
      ) : (
        <div className="history-list">
          {filteredEntries.map((entry) => {
            const currentSeverity = entrySeverity(entry);
            return (
              <div
                className="history-row"
                key={entry.id}
                role="button"
                tabIndex="0"
                onClick={() => onOpen(entry)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter' || event.key === ' ') onOpen(entry);
                }}
              >
                <span className="history-icon">▧</span>
                <span className="history-copy">
                  <strong>{entry.title}</strong>
                  <small>{new Date(entry.createdAt).toLocaleString()}</small>
                </span>
                <span className={`history-severity ${currentSeverity}`}>
                  {severityLabel(currentSeverity)}
                </span>
                <span className="history-status">Completed</span>
                <button
                  className="delete-button"
                  onClick={(event) => {
                    event.stopPropagation();
                    onDelete(entry.id);
                  }}
                >
                  Delete
                </button>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}
