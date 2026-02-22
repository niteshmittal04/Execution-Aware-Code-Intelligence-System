import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { useLocation } from 'react-router-dom';
import { explainFunction, explainSnippet } from '../api';
import { panelEnter } from '../animations/variants';
import Button from '../controls/Button';
import StatusMessage from '../components/StatusMessage';
import useAbortableAction from '../hooks/useAbortableAction';
import Panel from '../panel/Panel';
import { useSessionContext } from '../session/SessionContext';

function formatConfidence(confidence) {
  const score = Number(confidence);
  if (Number.isNaN(score)) {
    return 'Confidence unavailable';
  }
  return `Confidence ${(score * 100).toFixed(0)}%`;
}

function parseListItems(value) {
  const text = String(value ?? '').trim();
  if (!text) {
    return [];
  }

  const lines = text
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean);

  if (lines.length < 2) {
    return [];
  }

  const bulletPattern = /^([-*•]|\d+\.)\s+/;
  const allBulletLines = lines.every((line) => bulletPattern.test(line));
  if (!allBulletLines) {
    return [];
  }

  return lines.map((line) => line.replace(bulletPattern, '').trim()).filter(Boolean);
}

function renderSectionValue(value) {
  const items = parseListItems(value);
  if (items.length > 0) {
    return (
      <ul className="result-list">
        {items.map((item, index) => (
          <li key={`${item}-${index}`}>{item}</li>
        ))}
      </ul>
    );
  }

  return <p className="result-block">{value || 'Not available.'}</p>;
}

function ExplanationViewerPage() {
  const location = useLocation();
  const { activeSession } = useSessionContext();
  const [functionName, setFunctionName] = useState('');
  const [snippet, setSnippet] = useState('');
  const [explanation, setExplanation] = useState(null);
  const [status, setStatus] = useState({ type: '', text: '' });
  const [isFunctionLoading, setIsFunctionLoading] = useState(false);
  const [isSnippetLoading, setIsSnippetLoading] = useState(false);
  const runAbortableFunctionExplain = useAbortableAction();
  const runAbortableSnippetExplain = useAbortableAction();

  useEffect(() => {
    const searchParams = new URLSearchParams(location.search);
    const functionFromQuery = searchParams.get('fn');
    if (functionFromQuery) {
      setFunctionName(functionFromQuery);
    }
  }, [location.search]);

  useEffect(() => {
    const searchParams = new URLSearchParams(location.search);
    const functionFromQuery = searchParams.get('fn');
    if (functionFromQuery && activeSession?.session_id) {
      onExplainFunction(null, functionFromQuery);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeSession?.session_id, location.search]);

  const explanationSections = [
    { title: 'Summary', value: explanation?.summary },
    { title: 'Execution Flow', value: explanation?.execution_flow },
    { title: 'Dependencies', value: explanation?.dependencies },
    { title: 'Variables', value: explanation?.variables },
    { title: 'Improvements', value: explanation?.improvements },
    { title: 'Confidence', value: explanation?.confidence_score },
  ];

  async function onExplainFunction(event, overrideFunctionName = '') {
    if (event) {
      event.preventDefault();
    }
    if (!activeSession?.session_id) {
      setStatus({ type: 'error', text: 'No active repository session. Load a repository first.' });
      return;
    }
    const targetFunctionName = (overrideFunctionName || functionName).trim();
    if (!targetFunctionName) {
      setStatus({ type: 'error', text: 'Function name is required.' });
      return;
    }

    setStatus({ type: 'info', text: 'Generating function explanation...' });
    setIsFunctionLoading(true);
    try {
      const result = await runAbortableFunctionExplain((signal) => explainFunction(activeSession.session_id, targetFunctionName, { signal }));
      setExplanation(result);
      setStatus({ type: 'success', text: `Function explanation generated. ${formatConfidence(result?.confidence_score)}.` });
    } catch (err) {
      if (err.name === 'AbortError') {
        return;
      }
      setStatus({ type: 'error', text: `Function explanation failed: ${err.message}` });
    } finally {
      setIsFunctionLoading(false);
    }
  }

  async function onExplainSnippet(event) {
    event.preventDefault();
    if (!activeSession?.session_id) {
      setStatus({ type: 'error', text: 'No active repository session. Load a repository first.' });
      return;
    }
    setStatus({ type: 'info', text: 'Generating snippet explanation...' });
    setIsSnippetLoading(true);
    try {
      const result = await runAbortableSnippetExplain((signal) => explainSnippet(activeSession.session_id, snippet, 'python', { signal }));
      setExplanation(result);
      setStatus({ type: 'success', text: `Snippet explanation generated. ${formatConfidence(result?.confidence_score)}.` });
    } catch (err) {
      if (err.name === 'AbortError') {
        return;
      }
      setStatus({ type: 'error', text: `Snippet explanation failed: ${err.message}` });
    } finally {
      setIsSnippetLoading(false);
    }
  }

  return (
    <motion.section className="page" variants={panelEnter} initial="hidden" animate="visible">
      <h2>Explanation Viewer</h2>
      <p className="page-intro">Request execution-aware explanations by function name or by directly submitting a code snippet.</p>
      <div className="page-chips" aria-label="Explanation capabilities">
        <span className="chip">Execution Flow</span>
        <span className="chip">Dependencies</span>
        <span className="chip">Confidence Score</span>
      </div>
      <div className="grid-two">
        <Panel as="form" onSubmit={onExplainFunction} className="form-panel explanation-panel">
          <h3>Explain Function</h3>
          <input
            placeholder="module.function_name"
            value={functionName}
            onChange={(event) => setFunctionName(event.target.value)}
            required
          />
          <Button type="submit" disabled={isFunctionLoading}>{isFunctionLoading ? 'Explaining...' : 'Explain Function'}</Button>
        </Panel>
        <Panel as="form" onSubmit={onExplainSnippet} className="form-panel explanation-panel">
          <h3>Explain Snippet</h3>
          <textarea
            value={snippet}
            onChange={(event) => setSnippet(event.target.value)}
            rows={8}
            placeholder="Paste code snippet here..."
            required
          />
          <Button type="submit" disabled={isSnippetLoading}>{isSnippetLoading ? 'Explaining...' : 'Explain Snippet'}</Button>
        </Panel>
      </div>
      <StatusMessage type={status.type}>{status.text}</StatusMessage>
      {explanation && (
        <Panel className="explanation-panel">
          <h3>Explanation Output</h3>
          <div className="result-grid">
            {explanationSections.map((section) => (
              <article key={section.title} className="result-card">
                <h4>{section.title}</h4>
                {renderSectionValue(section.value)}
              </article>
            ))}
          </div>
        </Panel>
      )}
    </motion.section>
  );
}

export default ExplanationViewerPage;
