const stages = [
  ['1', 'clipboard', 'Triage Agent', 'Severity & Priority Classification'],
  ['2', 'search', 'Log Analysis Agent', 'Stack Trace & Failure Point Detection'],
  ['3', 'brain', 'Root Cause Agent', 'Evidence-Grounded Reasoning'],
  ['4', 'target', 'Duplicate Detection Agent', 'Historical Semantic Search'],
  ['5', 'tools', 'Remediation Agent', 'Fix Recommendation'],
];

export default function Pipeline({ isLoading, hasResult, activeStage = null, failed = false }) {
  const progress = hasResult ? 100 : isLoading && activeStage !== null ? activeStage * 20 : 0;

  return (
    <section className="panel pipeline-panel" aria-label="Multi-agent analysis pipeline">
      <div className="pipeline-heading">
        <div>
          <h2>
            <span>⌘</span> Multi-Agent Analysis Pipeline
          </h2>
          <p>AI agents working together to diagnose the issue</p>
        </div>
        <div className="pipeline-progress-wrap">
          <span>Overall Progress</span>
          <div className="pipeline-progress" aria-label={`Pipeline progress ${progress}%`}>
            <i style={{ width: `${progress}%` }} />
          </div>
          <b className="pipeline-percent">{progress}%</b>
        </div>
      </div>
      <div className="pipeline">
        {stages.map(([number, icon, title, description], index) => (
          <div className="pipeline-item" key={title}>
            <article
              className={`agent-card ${getStageStatus(index, { isLoading, hasResult, activeStage, failed })}`}
            >
              <div className="agent-number">{number}</div>
              <AgentIcon type={icon} />
              <h3>{title}</h3>
              <p>{description}</p>
              <span className="agent-status">
                {getStageLabel(index, { isLoading, hasResult, activeStage, failed })}
              </span>
            </article>
            {index < stages.length - 1 && (
              <span className="pipeline-arrow" aria-hidden="true">
                →
              </span>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}

function getStageStatus(index, { isLoading, hasResult, activeStage, failed }) {
  if (hasResult || (isLoading && activeStage !== null && index < activeStage)) return 'is-complete';
  if (failed && index === activeStage) return 'is-failed';
  if (isLoading && index === activeStage) return 'is-running';
  return 'is-waiting';
}

function getStageLabel(index, state) {
  const status = getStageStatus(index, state);
  if (status === 'is-complete') return 'Completed';
  if (status === 'is-failed') return 'Failed';
  if (status === 'is-running') return 'Analyzing...';
  return 'Waiting';
}

function AgentIcon({ type }) {
  const common = { className: 'agent-icon', viewBox: '0 0 32 32', 'aria-hidden': true };
  if (type === 'clipboard')
    return (
      <svg {...common}>
        <rect x="8" y="6" width="16" height="22" rx="1" />
        <path d="M12 6V3h8v3M12 12h8M12 17h8M12 22h5" />
      </svg>
    );
  if (type === 'search')
    return (
      <svg {...common}>
        <circle cx="14" cy="14" r="8" />
        <path d="m20 20 7 7M14 10v8M10 14h8" />
      </svg>
    );
  if (type === 'brain')
    return (
      <svg {...common}>
        <path d="M14 6a5 5 0 0 0-5 5 5 5 0 0 0 1 9 5 5 0 0 0 5 6V6ZM18 6a5 5 0 0 1 5 5 5 5 0 0 1-1 9 5 5 0 0 1-5 6V6ZM14 12h4M14 17h4M14 22h4" />
      </svg>
    );
  if (type === 'target')
    return (
      <svg {...common}>
        <circle cx="16" cy="16" r="11" />
        <circle cx="16" cy="16" r="6" />
        <circle cx="16" cy="16" r="2" />
        <path d="M16 2v5M16 25v5M2 16h5M25 16h5" />
      </svg>
    );
  return (
    <svg {...common}>
      <path d="m7 25 9-9M5 12l5-5 5 5-5 5M18 22l5-5 5 5-5 5Z" />
      <path d="m17 7 8 8M22 5l5 5" />
    </svg>
  );
}
