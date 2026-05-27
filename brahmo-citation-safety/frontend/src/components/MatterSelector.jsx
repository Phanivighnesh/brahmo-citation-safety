export default function MatterSelector({ matters, selected, onSelect, query, onQueryChange }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4 space-y-3">
      <div>
        <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
          Legal Matter
        </label>
        <select
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand focus:border-transparent"
          value={selected?.id || ""}
          onChange={(e) => {
            const m = matters.find(m => m.id === parseInt(e.target.value));
            onSelect(m);
            if (m) onQueryChange(m.query);
          }}
        >
          <option value="">— Select a matter —</option>
          {matters.map(m => (
            <option key={m.id} value={m.id}>
              {m.title} · {m.practice} · {m.court}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
          Lawyer's Query
        </label>
        <textarea
          rows={3}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand resize-none"
          placeholder="Type a legal question or select a matter above…"
          value={query}
          onChange={(e) => onQueryChange(e.target.value)}
        />
      </div>
    </div>
  );
}
