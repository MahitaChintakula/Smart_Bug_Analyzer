import { useState } from 'react';
import { askBugChat } from '../services/api';

export default function Chatbot({ analysis, messages, onMessagesChange, embedded = false }) {
  const [draft, setDraft] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  async function send(event) {
    event.preventDefault();
    const question = draft.trim();
    if (!analysis || !question || isLoading) return;

    const previousMessages = messages || [];
    const userMessage = { role: 'user', content: question };
    const withUserMessage = [...previousMessages, userMessage];
    onMessagesChange(withUserMessage);
    setDraft('');
    setError('');
    setIsLoading(true);

    try {
      const answer = await askBugChat(analysis, previousMessages, question);
      onMessagesChange([...withUserMessage, { role: 'assistant', content: answer }]);
    } catch (requestError) {
      setError(requestError.message || 'Unable to get a chatbot response.');
    } finally {
      setIsLoading(false);
    }
  }

  function clearConversation() {
    onMessagesChange([]);
    setError('');
  }

  function handleInputKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      event.currentTarget.form?.requestSubmit();
    }
  }

  return (
    <section
      className={`${embedded ? '' : 'panel '}chat-panel ${!analysis ? 'chat-disabled' : ''}`}
      aria-label="AI assistant"
    >
      <div className="chat-header">
        <div>
          <p className="eyebrow">CONTEXT-AWARE ASSISTANT</p>
          <h2>
            <span>✦</span> Ask about this bug
          </h2>
          <p className="chat-context">Ask questions about diagnosis, fixes, and prevention.</p>
        </div>
        <button
          className="chat-clear"
          type="button"
          onClick={clearConversation}
          disabled={isLoading || !messages?.length}
        >
          Clear conversation
        </button>
      </div>
      <div className="chat-messages" aria-live="polite">
        {!analysis && (
          <p className="chat-empty">
            Analyze a bug first to start a contextual assistant conversation.
          </p>
        )}
        {analysis && !messages?.length && (
          <p className="chat-empty">
            Ask a specific follow-up about the root cause, similar bugs, severity, or recommended
            fix.
          </p>
        )}
        {messages?.map((message, index) => (
          <div
            className={`chat-message ${message.role === 'user' ? 'user' : 'assistant'}`}
            key={`${message.role}-${index}`}
          >
            <span className="chat-role">{message.role === 'user' ? 'You' : 'Assistant'}</span>
            <p>{message.content}</p>
          </div>
        ))}
        {isLoading && (
          <div className="chat-loading" role="status">
            <i /> Reviewing the analysis…
          </div>
        )}
      </div>
      {error && (
        <p className="chat-error" role="alert">
          {error}
        </p>
      )}
      <form className="chat-form" onSubmit={send}>
        <textarea
          className="chat-input"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={handleInputKeyDown}
          maxLength={1200}
          rows={2}
          placeholder={analysis ? 'Ask a follow-up question…' : 'Analyze a bug to enable chat…'}
          aria-label="Chat message"
          disabled={!analysis}
        />
        <button
          className="chat-send"
          type="submit"
          disabled={!analysis || isLoading || !draft.trim()}
        >
          Send
        </button>
      </form>
      <p className="chat-note">
        Responses use this analysis and the conversation above. Sending is always manual.
      </p>
    </section>
  );
}
