export default function ReportsView({ entries, onDownload, onOpen, onDelete }) {
  return (
    <section className="page-panel panel" id="reports">
      <div className="page-heading">
        <div>
          <p className="eyebrow">EXPORTS</p>
          <h2>Reports</h2>
        </div>
        <span className="count-pill">PDF ready</span>
      </div>
      {entries.length === 0 ? (
        <div className="empty-state">
          <span>▧</span>
          <h3>No reports yet</h3>
          <p>Analyze a bug to create a downloadable PDF report.</p>
        </div>
      ) : (
        <div className="history-list">
          {entries.map((entry) => (
            <div className="report-row" key={entry.id}>
              <span className="report-icon">PDF</span>
              <span className="history-copy">
                <strong>{entry.title}</strong>
                <small>{new Date(entry.createdAt).toLocaleString()}</small>
              </span>
              <div className="report-actions">
                <button onClick={() => onOpen(entry)}>View</button>
                <button className="download-small" onClick={() => onDownload(entry)}>
                  Download PDF
                </button>
                <button className="delete-button" onClick={() => onDelete(entry.id)}>
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
