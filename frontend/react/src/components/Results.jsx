function percent(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return '—';
  return `${Math.round(number <= 1 ? number * 100 : number)}%`;
}

function valueOrUnknown(value, fallback = 'Not detected') {
  return value === undefined || value === null || value === '' ? fallback : value;
}

function severityClass(value) {
  const normalized = String(value || '')
    .trim()
    .toLowerCase();
  return ['critical', 'high', 'medium', 'low'].includes(normalized) ? normalized : 'unknown';
}

function Section({ number, icon, title, children }) {
  return (
    <section className="result-section">
      <h2>
        <span>{icon}</span> {number}. {title}
      </h2>
      {children}
    </section>
  );
}

function reportDescription(bugReport, logInfo) {
  const lines = String(bugReport || '')
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
  const description = lines.find((line) => !/Exception$/.test(line) && !/^at\s/i.test(line));
  if (description) return description;
  return `${valueOrUnknown(logInfo.exception)} at ${valueOrUnknown(logInfo.file)}:${valueOrUnknown(logInfo.line)}`;
}

function logExplanation(logInfo) {
  const exception = valueOrUnknown(logInfo.exception);
  const file = valueOrUnknown(logInfo.file);
  const line = valueOrUnknown(logInfo.line);
  return `The parser detected ${exception} at ${file}, line ${line}. This identifies the failure point in the submitted log and narrows the code path that needs investigation.`;
}

function duplicateExplanation(similarBugs) {
  if (!similarBugs.length)
    return 'Semantic search found no historical matches, so this issue may represent a new pattern for the team.';
  const strongest = similarBugs[0];
  const recurring =
    similarBugs.length > 1
      ? 'Several related records were retrieved, which suggests this failure pattern may recur across the system.'
      : 'The retrieved record is the closest known historical example and should be reviewed before implementing a new fix.';
  return `Semantic search found ${similarBugs.length} historical match${similarBugs.length === 1 ? '' : 'es'}. The strongest match is ${valueOrUnknown(strongest.bug_id)} — ${valueOrUnknown(strongest.title)} at ${percent(strongest.similarity_score)} similarity. ${recurring}`;
}

function overallSummary({ bugReport, logInfo, similarBugs, rootCause, triage, remediation }) {
  const issue = reportDescription(bugReport, logInfo);
  const matches = similarBugs.length
    ? `Similar historical bugs were found, including ${similarBugs
        .slice(0, 3)
        .map((bug) => bug.bug_id)
        .join(', ')}.`
    : 'No sufficiently similar historical bug was found.';
  return `${issue} The probable root cause is ${valueOrUnknown(rootCause.root_cause)}. ${matches} The issue is classified as ${valueOrUnknown(triage.severity)} severity with ${valueOrUnknown(triage.priority)} priority. Recommended fix: ${valueOrUnknown(remediation.recommended_fix)} Key prevention advice: ${valueOrUnknown(remediation.prevention)}`;
}

export default function Results({ analysis, bugReport, onDownload }) {
  if (!analysis) return null;

  const {
    log_info: logInfo = {},
    similar_bugs: similarBugs = [],
    root_cause: rootCause = {},
    triage = {},
    remediation = {},
  } = analysis;
  const severity = valueOrUnknown(triage.severity);
  const priority = valueOrUnknown(triage.priority);
  const codeSuggestion = valueOrUnknown(remediation.code_suggestion, 'Code suggestion unavailable');
  const fixConfidence = valueOrUnknown(remediation.fix_confidence, 'Unavailable');

  return (
    <section className="panel results-panel" aria-live="polite">
      <div className="results-heading">
        <h2 className="results-title">
          <span>▧</span> Bug Analysis Results
        </h2>
        <button className="pdf-button" onClick={() => onDownload(analysis, bugReport)}>
          ⇩ Download Report PDF
        </button>
      </div>
      <Section number="1" icon="🚦" title="Triage Agent">
        <div className="result-card triage-grid">
          <div>
            <p className="label accent">Classification Reason</p>
            <p>{valueOrUnknown(triage.reason)}</p>
            <p className="agent-explanation">
              The {severity} severity and {priority} priority reflect the impact described in the
              submitted report and the risk of leaving this issue unresolved.
            </p>
          </div>
          <div className="status-metric">
            <span>Severity</span>
            <strong className={`severity ${severityClass(triage.severity)}`}>{severity}</strong>
          </div>
          <div className="status-metric">
            <span>Priority</span>
            <strong className="priority">{priority}</strong>
          </div>
        </div>
      </Section>
      <Section number="2" icon="▣" title="Log Analysis Agent">
        <div className="result-card log-grid">
          <div>
            <p className="label accent">Key Error / Exception</p>
            <p>{valueOrUnknown(logInfo.exception)}</p>
          </div>
          <div>
            <p className="label">File</p>
            <p>{valueOrUnknown(logInfo.file)}</p>
          </div>
          <div>
            <p className="label">Line</p>
            <p>{valueOrUnknown(logInfo.line)}</p>
          </div>
          <p className="agent-explanation log-explanation">{logExplanation(logInfo)}</p>
        </div>
      </Section>
      <Section number="3" icon="♧" title="Root Cause Agent">
        <div className="result-card root-grid">
          <div>
            <p className="label accent">Probable Root Cause</p>
            <p>{valueOrUnknown(rootCause.root_cause)}</p>
            <p className="label accent confidence">Confidence</p>
            <p>{percent(rootCause.confidence)}</p>
            <p className="label">Explanation</p>
            <p>{valueOrUnknown(rootCause.explanation)}</p>
            <p className="agent-explanation">
              Evidence considered:{' '}
              {similarBugs.length
                ? similarBugs
                    .slice(0, 3)
                    .map((bug) => bug.bug_id)
                    .join(', ')
                : 'the submitted log and error details, with no close historical match'}
              .
            </p>
          </div>
        </div>
      </Section>
      <Section number="4" icon="◎" title="Duplicate Detection Agent">
        <div className="result-card">
          <p className="label accent">Historical Search Explanation</p>
          <p className="agent-explanation">{duplicateExplanation(similarBugs)}</p>
          <p className="label accent">Top Matches</p>
          <SimilarBugs bugs={similarBugs} />
        </div>
      </Section>
      <Section number="5" icon="⚒" title="Remediation Agent">
        <div className="result-card remediation">
          <p className="label accent">Recommended Fix</p>
          <p>{valueOrUnknown(remediation.recommended_fix)}</p>
          <p className="label accent">Code Suggestion</p>
          <pre className="code-suggestion">
            <code>{codeSuggestion}</code>
          </pre>
          <p className="label accent">Fix Confidence</p>
          <p className={`fix-confidence ${String(fixConfidence).toLowerCase()}`}>{fixConfidence}</p>
          {remediation.steps?.length > 0 && (
            <>
              <p className="label accent">Fix Steps</p>
              <ol>
                {remediation.steps.map((step, index) => (
                  <li key={`${index}-${step}`}>{step}</li>
                ))}
              </ol>
            </>
          )}
          <p className="label accent">Prevention</p>
          <p>{valueOrUnknown(remediation.prevention)}</p>
        </div>
      </Section>
      <Section number="6" icon="✓" title="Overall Summary">
        <div className="result-card overall-summary">
          <p>
            {overallSummary({ bugReport, logInfo, similarBugs, rootCause, triage, remediation })}
          </p>
        </div>
      </Section>
    </section>
  );
}

function SimilarBugs({ bugs, compact = false }) {
  if (!bugs.length) return <p className="muted">No matching historical bugs were returned.</p>;
  return (
    <div className={`similar-bugs ${compact ? 'compact' : ''}`}>
      {bugs.slice(0, 3).map((bug) => (
        <div className="similar-bug" key={bug.bug_id}>
          <span>
            <b>{bug.bug_id}</b>
            <em>·</em>
            {bug.title}
          </span>
          <strong>{percent(bug.similarity_score)} Match</strong>
        </div>
      ))}
    </div>
  );
}
