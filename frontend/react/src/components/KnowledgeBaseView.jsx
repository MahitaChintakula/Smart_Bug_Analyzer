import { useCallback, useEffect, useState } from 'react';
import {
  addKnowledgeBaseEntry,
  getKnowledgeBase,
  getKnowledgeBaseStats,
  rebuildKnowledgeBase,
} from '../services/api';

const EMPTY_ENTRY = {
  bug_id: '',
  title: '',
  description: '',
  severity: 'Medium',
  priority: 'P3',
  module: '',
  exception: '',
  stack_trace: '',
  root_cause: '',
  resolution: '',
  tags: '',
};

const SEVERITIES = ['Critical', 'High', 'Medium', 'Low'];

function similarityLabel(value) {
  return value === undefined || value === null ? 'Indexed' : `${Math.round(value * 100)}% match`;
}

export default function KnowledgeBaseView() {
  const [items, setItems] = useState([]);
  const [query, setQuery] = useState('');
  const [appliedQuery, setAppliedQuery] = useState('');
  const [severity, setSeverity] = useState('');
  const [stats, setStats] = useState(null);
  const [form, setForm] = useState(EMPTY_ENTRY);
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [rebuilding, setRebuilding] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const loadEntries = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const payload = await getKnowledgeBase({
        query: appliedQuery,
        severity,
      });
      setItems(payload.items || []);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }, [appliedQuery, severity]);

  const loadStats = useCallback(async () => {
    try {
      setStats(await getKnowledgeBaseStats());
    } catch (requestError) {
      setError(requestError.message);
    }
  }, []);

  useEffect(() => {
    loadEntries();
  }, [loadEntries]);

  useEffect(() => {
    loadStats();
  }, [loadStats]);

  function updateField(event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  }

  function submitSearch(event) {
    event.preventDefault();
    setAppliedQuery(query.trim());
  }

  function clearFilters() {
    setQuery('');
    setAppliedQuery('');
    setSeverity('');
    setNotice('');
  }

  async function handleRebuild() {
    setRebuilding(true);
    setError('');
    setNotice('');
    try {
      const result = await rebuildKnowledgeBase();
      setStats(result);
      setNotice('FAISS index rebuilt from the latest historical bug records.');
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setRebuilding(false);
    }
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setSaving(true);
    setError('');
    setNotice('');
    try {
      const result = await addKnowledgeBaseEntry({
        ...form,
        tags: form.tags
          .split(',')
          .map((tag) => tag.trim())
          .filter(Boolean),
      });
      setForm(EMPTY_ENTRY);
      setShowForm(false);
      setNotice(`${result.bug.bug_id} was added and indexed successfully.`);
      await loadEntries();
      await loadStats();
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="page-panel panel knowledge-page" id="knowledge-base">
      <div className="page-heading">
        <div>
          <p className="eyebrow">RAG KNOWLEDGE</p>
          <h2>Knowledge Base</h2>
          <p className="page-subtitle">
            Browse resolved bugs that ground root-cause analysis and fix recommendations.
          </p>
        </div>
        <div className="knowledge-heading-actions">
          <span className="count-pill">{stats?.total_bugs ?? '—'} records</span>
          <button
            className="secondary-action"
            type="button"
            onClick={handleRebuild}
            disabled={rebuilding}
          >
            {rebuilding ? 'Rebuilding…' : '↻ Rebuild Index'}
          </button>
        </div>
      </div>

      <div className="knowledge-stats">
        <div className="knowledge-stat">
          <span>Total historical bugs</span>
          <strong>{stats?.total_bugs ?? '—'}</strong>
          <small>Persisted in resolved_bugs.json</small>
        </div>
        <div className="knowledge-stat">
          <span>Indexed vectors</span>
          <strong>{stats?.indexed_vectors ?? '—'}</strong>
          <small>Available for FAISS retrieval</small>
        </div>
        <div className="knowledge-stat">
          <span>Vector dimension</span>
          <strong>{stats?.dimension ?? '—'}</strong>
          <small>Embedding representation</small>
        </div>
      </div>

      <div className="knowledge-toolbar">
        <form className="knowledge-search" onSubmit={submitSearch}>
          <span>⌕</span>
          <input
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search titles, causes, resolutions, or stack traces..."
            aria-label="Search the knowledge base"
          />
          <button type="submit">Search</button>
        </form>
        <label className="knowledge-filter">
          <span>Severity</span>
          <select value={severity} onChange={(event) => setSeverity(event.target.value)}>
            <option value="">All severities</option>
            {SEVERITIES.map((value) => (
              <option value={value} key={value}>
                {value}
              </option>
            ))}
          </select>
        </label>
        {(appliedQuery || severity) && (
          <button className="clear-filter-button" type="button" onClick={clearFilters}>
            Clear
          </button>
        )}
      </div>

      <div className="knowledge-actions-row">
        <span>
          {appliedQuery
            ? `Semantic matches for “${appliedQuery}”`
            : `${items.length} records shown`}
        </span>
        <button
          className="primary-action"
          type="button"
          onClick={() => setShowForm((open) => !open)}
        >
          {showForm ? 'Close Form' : '+ Add Resolved Bug'}
        </button>
      </div>

      {notice && <p className="knowledge-notice">✓ {notice}</p>}
      {error && (
        <p className="error knowledge-error" role="alert">
          {error}
        </p>
      )}

      {showForm && (
        <form className="knowledge-form" onSubmit={handleSubmit}>
          <div className="knowledge-form-heading">
            <div>
              <p className="eyebrow">MANUAL ENTRY</p>
              <h3>Add a Resolved Bug</h3>
            </div>
            <small>Leave Bug ID empty to generate the next available ID.</small>
          </div>
          <div className="knowledge-form-grid">
            <label>
              <span>Title *</span>
              <input name="title" value={form.title} onChange={updateField} required />
            </label>
            <label>
              <span>Bug ID</span>
              <input
                name="bug_id"
                value={form.bug_id}
                onChange={updateField}
                placeholder="Auto-generated"
              />
            </label>
            <label>
              <span>Severity</span>
              <select name="severity" value={form.severity} onChange={updateField}>
                {SEVERITIES.map((value) => (
                  <option value={value} key={value}>
                    {value}
                  </option>
                ))}
              </select>
            </label>
            <label>
              <span>Priority</span>
              <select name="priority" value={form.priority} onChange={updateField}>
                {['P1', 'P2', 'P3', 'P4'].map((value) => (
                  <option value={value} key={value}>
                    {value}
                  </option>
                ))}
              </select>
            </label>
            <label>
              <span>Module</span>
              <input
                name="module"
                value={form.module}
                onChange={updateField}
                placeholder="e.g. Authentication"
              />
            </label>
            <label>
              <span>Exception</span>
              <input name="exception" value={form.exception} onChange={updateField} />
            </label>
          </div>
          <label>
            <span>Description *</span>
            <textarea
              name="description"
              value={form.description}
              onChange={updateField}
              required
              rows={3}
            />
          </label>
          <div className="knowledge-form-grid two-columns">
            <label>
              <span>Stack Trace</span>
              <textarea
                name="stack_trace"
                value={form.stack_trace}
                onChange={updateField}
                rows={4}
              />
            </label>
            <label>
              <span>Root Cause</span>
              <textarea name="root_cause" value={form.root_cause} onChange={updateField} rows={4} />
            </label>
            <label>
              <span>Resolution</span>
              <textarea name="resolution" value={form.resolution} onChange={updateField} rows={4} />
            </label>
            <label>
              <span>
                Tags <small>(comma separated)</small>
              </span>
              <input
                name="tags"
                value={form.tags}
                onChange={updateField}
                placeholder="database, timeout"
              />
            </label>
          </div>
          <div className="knowledge-form-actions">
            <button className="secondary-action" type="button" onClick={() => setShowForm(false)}>
              Cancel
            </button>
            <button className="primary-action" type="submit" disabled={saving}>
              {saving ? 'Saving…' : 'Save and Index Bug'}
            </button>
          </div>
        </form>
      )}

      {loading ? (
        <div className="empty-state">
          <span>◌</span>
          <h3>Loading knowledge base</h3>
          <p>Reading historical bugs and retrieval metadata.</p>
        </div>
      ) : items.length === 0 ? (
        <div className="empty-state">
          <span>⌕</span>
          <h3>No matching historical bugs</h3>
          <p>Try a different query or add a resolved bug manually.</p>
        </div>
      ) : (
        <div className="knowledge-list">
          {items.map((bug) => (
            <article className="knowledge-card" key={bug.bug_id}>
              <div className="knowledge-card-heading">
                <div>
                  <span className="knowledge-id">{bug.bug_id}</span>
                  <h3>{bug.title}</h3>
                </div>
                <div className="knowledge-card-badges">
                  {bug.similarity !== undefined && (
                    <span className="knowledge-match">{similarityLabel(bug.similarity)}</span>
                  )}
                  <span className={`knowledge-severity ${String(bug.severity).toLowerCase()}`}>
                    {bug.severity}
                  </span>
                </div>
              </div>
              <div className="knowledge-meta">
                <span>Module: {bug.module || 'Unknown'}</span>
                <span>Priority: {bug.priority || 'Unknown'}</span>
                <span>Exception: {bug.exception || 'Unknown'}</span>
              </div>
              <p className="knowledge-description">{bug.description}</p>
              <div className="knowledge-resolution">
                <span>Historical Resolution</span>
                <p>{bug.resolution || 'No resolution recorded.'}</p>
              </div>
              {bug.root_cause && bug.root_cause !== 'Unknown' && (
                <div className="knowledge-root-cause">
                  <span>Root Cause</span>
                  <p>{bug.root_cause}</p>
                </div>
              )}
              {bug.tags?.length > 0 && (
                <div className="knowledge-tags">
                  {bug.tags.map((tag) => (
                    <span key={tag}>{tag}</span>
                  ))}
                </div>
              )}
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
