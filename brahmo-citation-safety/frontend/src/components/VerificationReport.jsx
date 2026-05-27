// Strip HTML tags returned by IK API (e.g. "<b>2000</b>" → "2000")
function stripHtml(str) {
  if (!str) return str;
  return str.replace(/<[^>]*>/g, "").replace(/\s+/g, " ").trim();
}

const HALT_LABELS = {
  FUTURE_YEAR:       "Future year — cannot exist",
  IMPOSSIBLE_VOLUME: "Impossible SCC volume — hallucinated",
  IMPOSSIBLE_PAGE:   "Page number too high — suspicious",
  PRE_MODERN_DATE:   "Pre-1900 date — suspicious",
};

export default function VerificationReport({ report, onCopyToNotes }) {
  if (!report) return null;

  const stats = [
    { label: "Total Found",   value: report.total,            color: "text-gray-700" },
    { label: "✅ Verified",   value: report.verified,         color: "text-green-700" },
    { label: "⚠️ Corrected",  value: report.corrected,        color: "text-blue-700" },
    { label: "⚠️ Unverified", value: report.unverified,       color: "text-yellow-700" },
    { label: "❌ Removed",    value: report.removed,          color: "text-red-700" },
    { label: "🛡️ Pre-filter", value: report.prefilter_caught, color: "text-purple-700" },
    { label: "🌐 IK Calls",   value: report.ik_calls,         color: "text-gray-700" },
    { label: "💰 Cost",       value: `₹${report.total_cost_inr.toFixed(2)}`, color: "text-gray-700" },
    {
      label: "🎯 Accuracy",
      value: `${report.accuracy_pct}%`,
      color: report.accuracy_pct === 100
        ? "text-green-700 font-bold"
        : report.accuracy_pct >= 70
        ? "text-orange-600 font-bold"
        : "text-red-700 font-bold",
    },
  ];

  return (
    <div className="mt-4 rounded-xl border border-gray-200 bg-white shadow-sm overflow-hidden">
      <div className="bg-gray-800 px-4 py-2">
        <h3 className="text-white font-semibold text-sm">📋 Citation Verification Report</h3>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-3 gap-px bg-gray-100 border-b border-gray-200">
        {stats.map((s) => (
          <div key={s.label} className="bg-white px-3 py-2 text-center">
            <div className={`text-lg font-bold ${s.color}`}>{s.value}</div>
            <div className="text-xs text-gray-500">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Citation rows */}
      {report.citations.length > 0 && (
        <div className="divide-y divide-gray-100">
          {report.citations.map((c, i) => (
            <CitationRow key={i} citation={c} onCopyToNotes={onCopyToNotes} />
          ))}
        </div>
      )}

      {/* Section alerts */}
      {report.section_alerts.length > 0 && (
        <div className="bg-amber-50 border-t border-amber-200 px-4 py-3">
          <p className="text-xs font-semibold text-amber-800 mb-2">
            ⚠️ SECTION ALERTS — Old Law → New Law
          </p>
          {report.section_alerts.map((a, i) => (
            <div key={i} className="flex items-center gap-2 text-xs text-amber-900 mb-1">
              <span className="font-mono bg-amber-100 px-1 rounded">{a.old_section}</span>
              <span>→</span>
              <span className="font-mono bg-green-100 px-1 rounded text-green-800">{a.new_section}</span>
              <span className="text-amber-600">
                ({a.old_act} → {a.new_act}, ×{a.occurrences})
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function CitationRow({ citation, onCopyToNotes }) {
  const config = {
    VERIFIED:   { bg: "bg-green-50",  border: "border-green-200",  badge: "badge-verified",   icon: "✅" },
    UNVERIFIED: { bg: "bg-yellow-50", border: "border-yellow-200", badge: "badge-unverified",  icon: "⚠️" },
    REMOVED:    { bg: "bg-red-50",    border: "border-red-200",    badge: "badge-removed",     icon: "❌" },
    CORRECTED:  { bg: "bg-blue-50",   border: "border-blue-200",   badge: "badge-corrected",   icon: "⚠️" },
  }[citation.status] || { bg: "bg-gray-50", border: "border-gray-200", badge: "", icon: "?" };

  const cleanName = stripHtml(citation.case_name);
  const haltLabel = citation.halt_reason
    ? (HALT_LABELS[citation.halt_reason] || citation.halt_reason.replace(/_/g, " "))
    : null;

  function handleCopy() {
    const text = cleanName
      ? `${citation.original_text} — ${cleanName}`
      : citation.original_text;
    onCopyToNotes?.({ text, time: new Date().toLocaleTimeString(), type: "citation" });
  }

  return (
    <div className={`px-4 py-2 ${config.bg} border-l-4 ${config.border}`}>
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <span className="font-mono text-xs text-gray-800 break-all">
            {citation.original_text}
          </span>
          {cleanName && (
            <p className="text-xs text-gray-500 mt-0.5 truncate">{cleanName}</p>
          )}
          {haltLabel && (
            <p className="text-xs text-red-600 mt-0.5 font-medium">⚡ {haltLabel}</p>
          )}
        </div>
        <div className="flex items-center gap-1.5 flex-shrink-0">
          {/* Copy to notes — only for VERIFIED citations */}
          {citation.status === "VERIFIED" && onCopyToNotes && (
            <button
              onClick={handleCopy}
              title="Copy citation to session notes"
              className="text-[10px] bg-gray-100 hover:bg-gray-200 text-gray-700 px-1.5 py-0.5 rounded border border-gray-300 transition-colors font-medium"
            >
              📝 Notes
            </button>
          )}
          <span className={`text-xs px-2 py-0.5 rounded-full font-medium whitespace-nowrap ${config.badge}`}>
            {config.icon} {citation.status}
          </span>
        </div>
      </div>
    </div>
  );
}
