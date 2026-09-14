import { useEffect, useRef, useState } from 'react';
import Pipeline from './components/Pipeline';
import Results from './components/Results';
import Chatbot from './components/Chatbot';
import HistoryView from './components/HistoryView';
import KnowledgeBaseView from './components/KnowledgeBaseView';
import ReportsView from './components/ReportsView';
import { analyzeBug, extractTextFromImage } from './services/api';
import { downloadAnalysisPdf } from './services/reportPdf';

const SUPPLIED_TEST_CASES = [
  `java.lang.NullPointerException
at LoginService.java:45

Login crashes because the user object is null.`,
  `java.sql.SQLTimeoutException
at UserRepository.java:88

The application cannot retrieve user details because database connections are timing out.`,
  `FileUploadException
at UploadController.java:67

Users are unable to upload files larger than the configured file size limit.`,
  `ImageDisplayException
at ProfileComponent.js:74

Users without profile pictures see a broken image icon instead of the default placeholder.`,
];

function asRecord(value) {
  return value && typeof value === 'object' && !Array.isArray(value) ? value : {};
}

function firstText(...values) {
  return values.find((value) => typeof value === 'string' && value.trim()) || '';
}

function normalizeRemediation(value) {
  const remediation = asRecord(value);
  const steps = Array.isArray(remediation.steps)
    ? remediation.steps
    : Array.isArray(remediation.fix_steps)
      ? remediation.fix_steps
      : [];

  return {
    ...remediation,
    recommended_fix: firstText(
      remediation.recommended_fix,
      remediation.recommendedFix,
      remediation.recommendation,
      remediation.fix,
    ),
    code_suggestion: firstText(
      remediation.code_suggestion,
      remediation.codeSuggestion,
      remediation.suggested_code,
      remediation.suggestedCode,
      remediation.code_snippet,
      remediation.codeSnippet,
      remediation.code,
    ),
    fix_confidence: firstText(
      remediation.fix_confidence,
      remediation.fixConfidence,
      remediation.confidence,
    ),
    steps,
    prevention: firstText(
      remediation.prevention,
      remediation.preventive_measures,
      remediation.preventiveMeasures,
    ),
  };
}

function normalizeAnalysis(value) {
  const analysis = asRecord(value);
  const remediationSources = [
    analysis.remediation,
    analysis.recommendation,
    analysis.fix_recommendation,
    analysis.fixRecommendation,
  ].map(normalizeRemediation);
  const remediation = {
    ...remediationSources[0],
    recommended_fix: firstText(...remediationSources.map((item) => item.recommended_fix)),
    code_suggestion: firstText(...remediationSources.map((item) => item.code_suggestion)),
    fix_confidence: firstText(...remediationSources.map((item) => item.fix_confidence)),
    steps: remediationSources.find((item) => item.steps?.length)?.steps || [],
    prevention: firstText(...remediationSources.map((item) => item.prevention)),
  };

  return { ...analysis, remediation };
}

function normalizeEntry(value) {
  const entry = asRecord(value);
  return {
    ...entry,
    bugReport: firstText(entry.bugReport, entry.bug_report, entry.report, entry.description),
    analysis: normalizeAnalysis(entry.analysis || entry.result || entry),
    chatMessages: Array.isArray(entry.chatMessages) ? entry.chatMessages : [],
  };
}

function loadEntries(storageKey) {
  try {
    const parsed = JSON.parse(localStorage.getItem(storageKey) || '[]');
    return Array.isArray(parsed) ? parsed.map(normalizeEntry) : [];
  } catch {
    return [];
  }
}

function mergeEntries(...entries) {
  const validEntries = entries.filter(Boolean).map(normalizeEntry);
  const newest = validEntries[0] || normalizeEntry({});
  const remediations = validEntries.map((entry) => entry.analysis.remediation);
  const remediation = {
    ...remediations[0],
    recommended_fix: firstText(...remediations.map((value) => value.recommended_fix)),
    code_suggestion: firstText(...remediations.map((value) => value.code_suggestion)),
    fix_confidence: firstText(...remediations.map((value) => value.fix_confidence)),
    steps: remediations.find((value) => value.steps?.length)?.steps || [],
    prevention: firstText(...remediations.map((value) => value.prevention)),
  };
  const sourceWithReport = validEntries.find((entry) => entry.bugReport);

  return normalizeEntry({
    ...newest,
    bugReport: sourceWithReport?.bugReport || newest.bugReport,
    analysis: {
      ...newest.analysis,
      remediation,
    },
  });
}

export default function App() {
  const [bugReport, setBugReport] = useState('');
  const [analysis, setAnalysis] = useState(null);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [page, setPage] = useState(() => window.location.hash.replace('#', '') || 'analyze');
  const [inputMode, setInputMode] = useState('paste');
  const [selectedFile, setSelectedFile] = useState(null);
  const [activeStage, setActiveStage] = useState(null);
  const [pipelineState, setPipelineState] = useState('idle');
  const [history, setHistory] = useState(() => loadEntries('smart-bug-history'));
  const [reports, setReports] = useState(() => loadEntries('smart-bug-reports'));
  const [chatMessages, setChatMessages] = useState([]);
  const [activeEntryId, setActiveEntryId] = useState(null);
  const [theme, setTheme] = useState(() => localStorage.getItem('smart-bug-theme') || 'dark');
  const fileInput = useRef(null);
  const ocrFileInput = useRef(null);
  const progressTimer = useRef(null);
  const dashboardTimer = useRef(null);
  const suppliedCaseIndex = useRef(0);

  useEffect(() => localStorage.setItem('smart-bug-history', JSON.stringify(history)), [history]);
  useEffect(() => localStorage.setItem('smart-bug-reports', JSON.stringify(reports)), [reports]);
  useEffect(() => {
    setReports((previous) =>
      previous.map((report) => {
        const matchingHistory = history.find((entry) => entry.id === report.id);
        const restoredReport = mergeEntries(report, matchingHistory);
        return JSON.stringify(restoredReport) === JSON.stringify(report) ? report : restoredReport;
      }),
    );
  }, [history]);
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem('smart-bug-theme', theme);
  }, [theme]);
  useEffect(
    () => () => {
      window.clearInterval(progressTimer.current);
      window.clearTimeout(dashboardTimer.current);
    },
    [],
  );

  async function submit(event) {
    event.preventDefault();
    const report = bugReport.trim();
    if (!report) {
      setError('Enter a bug report, error log, or stack trace before analyzing.');
      return;
    }
    setError('');
    setAnalysis(null);
    setChatMessages([]);
    setActiveEntryId(null);
    setIsLoading(true);
    setPipelineState('loading');
    setActiveStage(0);
    window.clearInterval(progressTimer.current);
    progressTimer.current = window.setInterval(
      () => setActiveStage((current) => (current === null || current >= 4 ? 4 : current + 1)),
      650,
    );
    try {
      const result = normalizeAnalysis(await analyzeBug(report));
      setAnalysis(result);
      const entryId = crypto.randomUUID();
      const entry = {
        id: entryId,
        title: result.log_info?.exception || report.split('\n')[0].slice(0, 60),
        bugReport: report,
        analysis: result,
        chatMessages: [],
        createdAt: new Date().toISOString(),
      };
      setActiveEntryId(entryId);
      setHistory((previous) => [entry, ...previous].slice(0, 30));
      setReports((previous) => [entry, ...previous].slice(0, 30));
      setPipelineState('success');
      setActiveStage(null);
      window.clearTimeout(dashboardTimer.current);
      dashboardTimer.current = window.setTimeout(() => navigate('dashboard'), 350);
    } catch (requestError) {
      setError(requestError.message);
      setPipelineState('failed');
    } finally {
      window.clearInterval(progressTimer.current);
      setIsLoading(false);
    }
  }

  function navigate(nextPage) {
    setPage(nextPage);
    window.history.replaceState(null, '', `#${nextPage}`);
  }

  function toggleTheme() {
    setTheme((current) => (current === 'dark' ? 'light' : 'dark'));
  }

  function clearWorkspace() {
    window.location.reload();
  }

  function openEntry(entry) {
    const savedHistoryEntry = history.find((candidate) => candidate.id === entry.id);
    const savedReportEntry = reports.find((candidate) => candidate.id === entry.id);
    const restoredEntry = mergeEntries(entry, savedHistoryEntry, savedReportEntry);

    setBugReport(restoredEntry.bugReport);
    setAnalysis(restoredEntry.analysis);
    setChatMessages(restoredEntry.chatMessages || []);
    setActiveEntryId(restoredEntry.id);
    setPipelineState('success');
    setActiveStage(null);
    navigate('dashboard');
  }

  function updateChatMessages(nextMessages) {
    setChatMessages(nextMessages);
    if (!activeEntryId) return;
    const update = (previous) =>
      previous.map((entry) =>
        entry.id === activeEntryId ? { ...entry, chatMessages: nextMessages } : entry,
      );
    setHistory(update);
    setReports(update);
  }

  function deleteHistoryEntry(id) {
    if (window.confirm('Delete this history item?'))
      setHistory((previous) => previous.filter((entry) => entry.id !== id));
  }

  function deleteReport(id) {
    if (window.confirm('Delete this report?'))
      setReports((previous) => previous.filter((entry) => entry.id !== id));
  }

  async function loadFile(file) {
    if (!file) return;
    if (file.size > 10 * 1024 * 1024) {
      setError('Please choose a file smaller than 10 MB.');
      return;
    }
    if (file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')) {
      setError(
        'PDF files can be selected, but the analyzer currently needs text content. Please upload a .txt, .log, .md, or .json file.',
      );
      return;
    }
    try {
      const contents = await file.text();
      if (!contents.trim()) {
        setError('The selected file is empty.');
        return;
      }
      setBugReport(contents.slice(0, 5000));
      setSelectedFile({ name: file.name, size: file.size });
      setError('');
      setInputMode('upload');
      navigate('analyze');
    } catch {
      setError('Unable to read that file. Please choose a text or log file.');
    }
  }

  async function loadScreenshot(file) {
    if (!file) return;
    if (file.size > 10 * 1024 * 1024) {
      setError('Please choose an image smaller than 10 MB.');
      return;
    }
    if (!file.type.startsWith('image/')) {
      setError('Please choose a PNG, JPEG, WEBP, or GIF screenshot.');
      return;
    }

    setError('');
    try {
      const result = await extractTextFromImage(file);
      const contents = result.text?.trim();
      if (!contents) {
        setError('No readable text was found in the screenshot.');
        return;
      }
      setBugReport(contents.slice(0, 5000));
      setSelectedFile({ name: file.name, size: file.size, ocr: true });
      setInputMode('upload');
      navigate('analyze');
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  function readFile(event) {
    const file = event.target.files?.[0];
    loadFile(file);
    event.target.value = '';
  }

  function readScreenshot(event) {
    const file = event.target.files?.[0];
    loadScreenshot(file);
    event.target.value = '';
  }

  function handleDrop(event) {
    event.preventDefault();
    const file = event.dataTransfer.files?.[0];
    if (!file) return;
    if (file.type.startsWith('image/')) {
      loadScreenshot(file);
    } else {
      loadFile(file);
    }
  }

  function useSuppliedTestCase() {
    const nextCase = SUPPLIED_TEST_CASES[suppliedCaseIndex.current];
    suppliedCaseIndex.current = (suppliedCaseIndex.current + 1) % SUPPLIED_TEST_CASES.length;
    setBugReport(nextCase);
    setSelectedFile(null);
    setInputMode('paste');
    setError('');
  }

  function downloadReport(entryOrAnalysis, report) {
    const entry = entryOrAnalysis.analysis ? entryOrAnalysis : null;
    downloadAnalysisPdf(entry ? entry.analysis : entryOrAnalysis, entry ? entry.bugReport : report);
  }

  function scrollToTop() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  const pageTitle =
    page === 'dashboard'
      ? 'Bug Analysis Results'
      : page === 'history'
        ? 'History'
        : page === 'reports'
          ? 'Reports'
          : page === 'knowledge'
            ? 'Knowledge Base'
            : page === 'settings'
              ? 'Settings'
              : 'AI Assistant';
  const navItems = [
    ['analyze', '⌁', 'Analyze Bug', 'Start new analysis'],
    ['dashboard', '▦', 'Dashboard', 'Analysis results'],
    ['history', '◴', 'History', 'Past analyses'],
    ['reports', '▤', 'Reports', 'Generated reports'],
    ['knowledge', '▧', 'Knowledge Base', 'Resolved bugs'],
    ['assistant', '✦', 'AI Assistant', 'Smart assistant'],
  ];
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand smart-brand" aria-label="Smart Bug Analyzer">
          <SmartBugMark />
          <span>
            <b>SMART BUG</b>
            <strong>ANALYZER</strong>
          </span>
        </div>
        <nav>
          {navItems.map(([id, icon, label, hint]) => (
            <button key={id} className={page === id ? 'active' : ''} onClick={() => navigate(id)}>
              <i>{icon}</i>
              <span>
                <b>
                  {label}
                  {label === 'AI Assistant' && <em>New</em>}
                </b>
                <small>{hint}</small>
              </span>
            </button>
          ))}
        </nav>
        <div className="system-status">
          <i /> <b>System Status</b>
          <small>All Systems Operational</small>
        </div>
      </aside>
      <main>
        <header
          className={`topbar ${page === 'dashboard' ? 'results-topbar' : ''} ${page === 'analyze' ? 'project-topbar' : ''}`}
        >
          {page === 'analyze' ? (
            <AnalyzeProjectHeader theme={theme} />
          ) : (
            <div className="topbar-title">
              <span>⌁</span>
              <h1>{pageTitle}</h1>
              <span>⌁</span>
            </div>
          )}
          <div className="top-actions">
            <button
              className="theme-switcher"
              type="button"
              onClick={toggleTheme}
              aria-label="Toggle theme"
            >
              {theme === 'dark' ? '☀' : '☾'}
            </button>
          </div>
        </header>
        <div key={page} className="page-transition">
          {page === 'analyze' && (
            <div className="analyze-workspace">
              <section className="panel input-panel" id="analyze">
                <form onSubmit={submit}>
                  <div className="describe-heading">
                    <span>⬡</span>
                    <div>
                      <h2>Describe the Bug</h2>
                      <p>Provide error details, logs, or upload files for analysis</p>
                    </div>
                    <div className="describe-actions">
                      <button
                        type="button"
                        onClick={() => {
                          setInputMode('upload');
                          fileInput.current?.click();
                        }}
                      >
                        ⇧ Upload File
                      </button>
                      <button type="button" onClick={() => ocrFileInput.current?.click()}>
                        ◉ Screenshot
                      </button>
                      <button type="button" onClick={clearWorkspace}>
                        ↻ Clear
                      </button>
                    </div>
                  </div>
                  <input
                    ref={fileInput}
                    hidden
                    type="file"
                    accept=".txt,.log,.json,.md,.csv,.py,.js,.jsx,.ts,.tsx,.c,.h,.cpp,.cc,.cxx,.hpp,.go,.rs,text/plain,application/json,application/pdf"
                    onChange={readFile}
                  />
                  <input
                    ref={ocrFileInput}
                    hidden
                    type="file"
                    accept="image/png,image/jpeg,image/webp,image/gif"
                    onChange={readScreenshot}
                  />
                  {inputMode === 'upload' && selectedFile ? (
                    <div className="selected-file">
                      ✓ {selectedFile.name}
                      {selectedFile.ocr ? ' · Text extracted' : ''}
                    </div>
                  ) : null}
                  <div className="composer">
                    <textarea
                      value={bugReport}
                      onChange={(event) => {
                        setBugReport(event.target.value);
                        setSelectedFile(null);
                        setInputMode('paste');
                      }}
                      maxLength="5000"
                      placeholder="Paste error logs, stack traces, or describe the issue..."
                      aria-label="Bug report"
                    />
                    <div className="composer-footer">
                      <span>{bugReport.length} / 5000</span>
                      <button disabled={isLoading} type="submit">
                        {isLoading ? 'Analyzing…' : 'Analyze Bug  ▷'}
                      </button>
                    </div>
                  </div>
                </form>
                {error && (
                  <p className="error" role="alert">
                    {error}
                  </p>
                )}
                <button className="example-link" type="button" onClick={useSuppliedTestCase}>
                  ✧ &nbsp;Try sample cases
                </button>
              </section>
              <Pipeline
                isLoading={isLoading}
                hasResult={Boolean(analysis)}
                activeStage={activeStage}
                failed={pipelineState === 'failed'}
              />
              <DashboardPreview entries={history} onNavigate={navigate} onOpen={openEntry} />
            </div>
          )}
          {page === 'dashboard' && (
            <DashboardFull
              entries={history}
              analysis={analysis}
              bugReport={bugReport}
              onNavigate={navigate}
              onOpen={openEntry}
              onDownload={downloadReport}
            />
          )}
          {page === 'history' && (
            <HistoryView entries={history} onOpen={openEntry} onDelete={deleteHistoryEntry} />
          )}
          {page === 'reports' && (
            <ReportsView
              entries={reports}
              onOpen={openEntry}
              onDownload={downloadReport}
              onDelete={deleteReport}
            />
          )}
          {page === 'assistant' && (
            <section className="page-panel panel assistant-page">
              <div className="page-heading">
                <div>
                  <p className="eyebrow">AI ASSISTANT</p>
                  <h2>Your analysis companion</h2>
                </div>
                <span className="count-pill">Beta</span>
              </div>
              <Chatbot
                analysis={analysis}
                messages={chatMessages}
                onMessagesChange={updateChatMessages}
                embedded
              />
            </section>
          )}
          {page === 'knowledge' && <KnowledgeBaseView />}
          {page === 'settings' && <EmptyWorkspace page={page} onNavigate={navigate} />}
        </div>
      </main>
      <button
        className="floating-scroll-button"
        type="button"
        onClick={scrollToTop}
        aria-label="Scroll to top"
      >
        ↑
      </button>
    </div>
  );
}

function localBugId(entry) {
  return (
    entry?.analysis?.bug_id || (entry?.id ? `#${String(entry.id).slice(0, 8).toUpperCase()}` : '—')
  );
}
function AnalyzeProjectHeader({ theme }) {
  return (
    <div className="project-header" aria-label="Creation of Intelligent Bug Diagnosis Platform">
      <CircuitArt side="left" theme={theme} />
      <div className="project-title">
        <span>Creation of Intelligent</span>
        <strong>Bug Diagnosis Platform</strong>
        <span>with Fix Recommendation Assistance</span>
      </div>
      <CircuitArt side="right" theme={theme} />
    </div>
  );
}

function DashboardPreview({ entries, onNavigate, onOpen }) {
  return (
    <section className="dashboard-preview">
      <div className="recent-panel panel">
        <div className="mini-heading">
          <h2>✧ &nbsp;Recent Analyses</h2>
          <button onClick={() => onNavigate('history')}>View all</button>
        </div>
        {entries.slice(0, 5).map((entry) => (
          <button
            className="recent-row"
            type="button"
            key={entry.id}
            onClick={() => onOpen?.(entry)}
          >
            <b>{localBugId(entry)}</b>
            <span>{entry.title}</span>
            <em className={(entry.analysis?.triage?.severity || 'low').toLowerCase()}>
              {entry.analysis?.triage?.severity || 'Saved'}
            </em>
            <small>{entry.analysis ? 'Completed' : 'Saved'}</small>
            <time>{entry.createdAt ? new Date(entry.createdAt).toLocaleDateString() : '—'}</time>
          </button>
        ))}
        {!entries.length && <p className="empty-mini">Completed analyses will appear here.</p>}
      </div>
      <Insights entries={entries} />
    </section>
  );
}
function Insights({ entries }) {
  const [period, setPeriod] = useState('week');
  const [periodMenuOpen, setPeriodMenuOpen] = useState(false);
  const now = new Date();
  const periodStart = new Date(now);
  periodStart.setHours(0, 0, 0, 0);
  if (period === 'month') {
    periodStart.setDate(1);
  } else {
    const mondayOffset = periodStart.getDay() === 0 ? 6 : periodStart.getDay() - 1;
    periodStart.setDate(periodStart.getDate() - mondayOffset);
  }
  const periodEntries = entries.filter((entry) => {
    const createdAt = entry.createdAt ? new Date(entry.createdAt) : null;
    return (
      createdAt &&
      !Number.isNaN(createdAt.getTime()) &&
      createdAt >= periodStart &&
      createdAt <= now
    );
  });
  const total = periodEntries.length;
  const critical = periodEntries.filter(
    (entry) => String(entry.analysis?.triage?.severity).toLowerCase() === 'critical',
  ).length;
  const medium = periodEntries.filter((entry) =>
    ['high', 'medium'].includes(String(entry.analysis?.triage?.severity).toLowerCase()),
  ).length;
  const low = periodEntries.filter(
    (entry) => String(entry.analysis?.triage?.severity).toLowerCase() === 'low',
  ).length;
  const other = Math.max(total - critical - medium - low, 0);
  const legend = [
    { label: 'Total Analysis', value: total, color: '#13b9b0', percent: total ? 100 : 0 },
    {
      label: 'Critical Issues',
      value: critical,
      color: '#f04d62',
      percent: total ? Math.round((critical / total) * 100) : 0,
    },
    {
      label: 'Medium Issues',
      value: medium,
      color: '#f4b51b',
      percent: total ? Math.round((medium / total) * 100) : 0,
    },
    {
      label: 'Low Issues',
      value: low,
      color: '#4bd15d',
      percent: total ? Math.round((low / total) * 100) : 0,
    },
  ];
  const segments = [
    { value: other, color: '#13b9b0' },
    { value: low, color: '#4bd15d' },
    { value: medium, color: '#f4b51b' },
    { value: critical, color: '#f04d62' },
  ].filter((segment) => segment.value > 0);
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  let offset = 0;

  const periodLabel = period === 'month' ? 'This Month' : 'This Week';
  return (
    <section className="insights-panel panel">
      <div className="mini-heading">
        <h2>Insights Overview</h2>
        <div className="insight-period">
          <button
            className="insight-period-toggle"
            type="button"
            aria-haspopup="menu"
            aria-expanded={periodMenuOpen}
            onClick={() => setPeriodMenuOpen((open) => !open)}
          >
            {periodLabel}⌄
          </button>
          {periodMenuOpen && (
            <div className="insight-period-menu" role="menu">
              <button
                type="button"
                role="menuitem"
                className={period === 'week' ? 'selected' : ''}
                onClick={() => {
                  setPeriod('week');
                  setPeriodMenuOpen(false);
                }}
              >
                This Week
              </button>
              <button
                type="button"
                role="menuitem"
                className={period === 'month' ? 'selected' : ''}
                onClick={() => {
                  setPeriod('month');
                  setPeriodMenuOpen(false);
                }}
              >
                This Month
              </button>
            </div>
          )}
        </div>
      </div>
      <div className="insights-visual">
        <div className="insight-donut-wrap">
          <svg
            className="insight-donut"
            viewBox="0 0 140 140"
            role="img"
            aria-label={`Severity distribution for ${total} analyses`}
          >
            <circle className="insight-donut-track" cx="70" cy="70" r={radius} />
            {segments.map((segment, index) => {
              const length = (segment.value / total) * circumference;
              const gap = Math.min(4, length * 0.08);
              const dash = Math.max(length - gap, 0);
              const dashOffset = -offset;
              offset += length;
              return (
                <circle
                  key={`${segment.color}-${index}`}
                  className="insight-donut-segment"
                  cx="70"
                  cy="70"
                  r={radius}
                  stroke={segment.color}
                  strokeDasharray={`${dash} ${circumference - dash}`}
                  strokeDashoffset={dashOffset}
                />
              );
            })}
          </svg>
          <div className="insight-donut-center">
            <span>Total Analysis</span>
            <b>{total}</b>
            <em>{total ? '100%' : '—'}</em>
          </div>
        </div>
        <div className="insight-legend">
          {legend.map((item) => (
            <div className="insight-legend-row" key={item.label}>
              <i style={{ backgroundColor: item.color }} />
              <span>{item.label}</span>
              <b>{item.value}</b>
              <em>{item.percent}%</em>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
function DashboardFull({ entries, analysis, bugReport, onNavigate, onOpen, onDownload }) {
  return analysis ? (
    <Results analysis={analysis} bugReport={bugReport} onDownload={onDownload} />
  ) : (
    <div className="dashboard-full">
      <div className="dashboard-hero">
        <p>Analysis Results</p>
        <h2>Select a completed analysis to view its findings</h2>
        <button onClick={() => onNavigate('analyze')}>Analyze a Bug &nbsp;→</button>
      </div>
      <DashboardPreview entries={entries} onNavigate={onNavigate} onOpen={onOpen} />
    </div>
  );
}
function EmptyWorkspace({ page, onNavigate }) {
  const copy =
    page === 'knowledge'
      ? [
          'Knowledge Base',
          'Resolved bugs and historical matches become available as analyses are completed.',
        ]
      : ['Settings', 'Application preferences, display mode, and workspace options.'];
  return (
    <section className="page-panel panel empty-workspace">
      <span>{page === 'knowledge' ? '▧' : '⚙'}</span>
      <h2>{copy[0]}</h2>
      <p>{copy[1]}</p>
      <button onClick={() => onNavigate('analyze')}>Analyze a Bug</button>
    </section>
  );
}
function SmartBugMark() {
  return (
    <img
      className="smart-bug-mark smart-bug-image"
      src="/bug-sidebar-icon.png"
      alt=""
      aria-hidden="true"
      draggable="false"
    />
  );
}

function CircuitArt({ side, theme }) {
  const variant = theme === 'dark' ? '-dark' : '';
  return (
    <img
      className={`circuit-art ${side}`}
      src={`/header-${side}-design${variant}.png`}
      alt=""
      aria-hidden="true"
      draggable="false"
    />
  );
}
