import { useState } from 'react';
import { explainFunction, explainSnippet } from '../api';

function ExplanationViewerPage() {
  const [functionName, setFunctionName] = useState('');
  const [snippet, setSnippet] = useState('');
  const [explanation, setExplanation] = useState(null);
  const [error, setError] = useState('');

  async function onExplainFunction(event) {
    event.preventDefault();
    setError('');
    try {
      setExplanation(await explainFunction(functionName));
    } catch (err) {
      setError(err.message);
    }
  }

  async function onExplainSnippet(event) {
    event.preventDefault();
    setError('');
    try {
      setExplanation(await explainSnippet(snippet, 'python'));
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <section>
      <h2>Explanation Viewer</h2>
      <div className="grid-two">
        <form onSubmit={onExplainFunction} className="panel">
          <h3>Explain Function</h3>
          <input value={functionName} onChange={(event) => setFunctionName(event.target.value)} required />
          <button type="submit">Explain Function</button>
        </form>
        <form onSubmit={onExplainSnippet} className="panel">
          <h3>Explain Snippet</h3>
          <textarea value={snippet} onChange={(event) => setSnippet(event.target.value)} rows={8} required />
          <button type="submit">Explain Snippet</button>
        </form>
      </div>
      {error && <p>{error}</p>}
      {explanation && (
        <div className="panel">
          <h3>Summary</h3>
          <p>{explanation.summary}</p>
          <h3>Execution Flow</h3>
          <p>{explanation.execution_flow}</p>
          <h3>Dependencies</h3>
          <p>{explanation.dependencies}</p>
          <h3>Variables</h3>
          <p>{explanation.variables}</p>
          <h3>Improvements</h3>
          <p>{explanation.improvements}</p>
          <h3>Confidence</h3>
          <p>{explanation.confidence_score}</p>
        </div>
      )}
    </section>
  );
}

export default ExplanationViewerPage;
