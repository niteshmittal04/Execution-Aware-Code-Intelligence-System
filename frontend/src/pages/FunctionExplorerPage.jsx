import { useState } from 'react';
import { fetchGraph } from '../api';

function FunctionExplorerPage() {
  const [functionName, setFunctionName] = useState('');
  const [fileTree, setFileTree] = useState([]);
  const [functions, setFunctions] = useState([]);
  const [error, setError] = useState('');

  async function onLoad(event) {
    event.preventDefault();
    setError('');
    try {
      const graph = await fetchGraph(functionName);
      const files = [...new Set(graph.nodes.map((node) => node.file))];
      setFileTree(files);
      setFunctions(graph.nodes.filter((node) => node.type === 'function').map((node) => node.id));
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <section>
      <h2>Function Explorer</h2>
      <form onSubmit={onLoad} className="panel">
        <label>
          Function name
          <input value={functionName} onChange={(event) => setFunctionName(event.target.value)} required />
        </label>
        <button type="submit">Load</button>
      </form>
      {error && <p>{error}</p>}
      <div className="grid-two">
        <div className="panel">
          <h3>File Tree</h3>
          <ul>{fileTree.map((item) => <li key={item}>{item}</li>)}</ul>
        </div>
        <div className="panel">
          <h3>Functions List</h3>
          <ul>{functions.map((item) => <li key={item}>{item}</li>)}</ul>
        </div>
      </div>
    </section>
  );
}

export default FunctionExplorerPage;
