function ListPanel({ title, count, items, emptyText }) {
  return (
    <div className="panel">
      <h3 className="panel-heading">
        {title} <span>{count}</span>
      </h3>
      {items.length === 0 ? (
        <p className="empty-state">{emptyText}</p>
      ) : (
        <ul>
          {items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default ListPanel;
