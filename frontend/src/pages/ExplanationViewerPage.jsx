import { useState } from 'react';
import { explainFunction, explainSnippet } from '../api';
import StatusMessage from '../components/StatusMessage';
import useAbortableAction from '../hooks/useAbortableAction';

function ExplanationViewerPage() {
  const [functionName, setFunctionName] = useState('');
  const [snippet, setSnippet] = useState('');
  const [explanation, setExplanation] = useState(null);
  const [error, setError] = useState('');
  const [isFunctionLoading, setIsFunctionLoading] = useState(false);
  const [isSnippetLoading, setIsSnippetLoading] = useState(false);
  const runAbortableFunctionExplain = useAbortableAction();
  const runAbortableSnippetExplain = useAbortableAction();

  const explanationSections = [
    { title: 'Summary', value: explanation?.summary },
    { title: 'Execution Flow', value: explanation?.execution_flow },
    { title: 'Dependencies', value: explanation?.dependencies },
    { title: 'Variables', value: explanation?.variables },
    { title: 'Improvements', value: explanation?.improvements },
    { title: 'Confidence', value: explanation?.confidence_score },
  ];

  async function onExplainFunction(event) {
    event.preventDefault();
    setError('');
    setIsFunctionLoading(true);
    try {
      setExplanation(await runAbortableFunctionExplain((signal) => explainFunction(functionName, { signal })));
    } catch (err) {
      if (err.name === 'AbortError') {
        return;
      }
      setError(err.message);
    } finally {
      setIsFunctionLoading(false);
    }
  }

  async function onExplainSnippet(event) {
    event.preventDefault();
    setError('');
    setIsSnippetLoading(true);
    try {
      setExplanation(await runAbortableSnippetExplain((signal) => explainSnippet(snippet, 'python', { signal })));
    } catch (err) {
      if (err.name === 'AbortError') {
        return;
      }
      setError(err.message);
    } finally {
      setIsSnippetLoading(false);
    }
  }

  return (
    <section className="page">
      <h2>Explanation Viewer</h2>
      <p className="page-intro">Request execution-aware explanations by function name or by directly submitting a code snippet.</p>
      <div className="page-chips" aria-label="Explanation capabilities">
        <span className="chip">Execution Flow</span>
        <span className="chip">Dependencies</span>
        <span className="chip">Confidence Score</span>
      </div>
      <div className="grid-two">
        <form onSubmit={onExplainFunction} className="panel form-panel">
          <h3>Explain Function</h3>
          <input
            placeholder="module.function_name"
            value={functionName}
            onChange={(event) => setFunctionName(event.target.value)}
            required
          />
          <button type="submit" disabled={isFunctionLoading}>{isFunctionLoading ? 'Explaining...' : 'Explain Function'}</button>
        </form>
        <form onSubmit={onExplainSnippet} className="panel form-panel">
          <h3>Explain Snippet</h3>
          <textarea
            value={snippet}
            onChange={(event) => setSnippet(event.target.value)}
            rows={8}
            placeholder="Paste code snippet here..."
            required
          />
          <button type="submit" disabled={isSnippetLoading}>{isSnippetLoading ? 'Explaining...' : 'Explain Snippet'}</button>
        </form>
      </div>
      <StatusMessage type="error">{error}</StatusMessage>
      {explanation && (
        <div className="panel explanation-panel">
          <h3>Explanation Output</h3>
          <div className="result-grid">
            {explanationSections.map((section) => (
              <article key={section.title} className="result-card">
                <h4>{section.title}</h4>
                <p className="result-block">{section.value || 'Not available.'}</p>
              </article>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}

export default ExplanationViewerPage;
