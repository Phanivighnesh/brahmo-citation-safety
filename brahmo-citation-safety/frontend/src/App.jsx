import { useState, useEffect } from "react";
import { fetchMatters, fetchHealth, fetchCompare } from "./api";
import MatterSelector from "./components/MatterSelector";
import ResponsePanel from "./components/ResponsePanel";
import VerificationReport from "./components/VerificationReport";
import StatusBar from "./components/StatusBar";
import SessionNotes from "./components/SessionNotes";

export default function App() {
  const [matters,  setMatters]  = useState([]);
  const [health,   setHealth]   = useState(null);
  const [selected, setSelected] = useState(null);
  const [query,    setQuery]    = useState("");
  const [result,   setResult]   = useState(null);
  const [loading,  setLoading]  = useState(false);
  const [error,    setError]    = useState(null);
  const [step,     setStep]     = useState("");

  // ── Session notes — persists across queries, resets on page refresh ──────────
  const [notes, setNotes] = useState([]);

  function addNote(note) {
    setNotes(prev => [...prev, note]);
  }

  function clearNotes() {
    setNotes([]);
  }

  useEffect(() => {
    fetchMatters().then(setMatters).catch(console.error);
    fetchHealth().then(setHealth).catch(console.error);
  }, []);

  async function handleCompare() {
    if (!query.trim()) return;
    setLoading(true);
    setResult(null);
    setError(null);

    const steps = [
      "Sending query to Gemini…",
      "Extracting citations…",
      "Running hallucination pre-filter…",
      "Verifying against Indian Kanoon…",
      "Annotating response…",
    ];

    let i = 0;
    setStep(steps[0]);
    const ticker = setInterval(() => {
      i = Math.min(i + 1, steps.length - 1);
      setStep(steps[i]);
    }, 1800);

    try {
      const data = await fetchCompare(query);
      setResult(data);
    } catch (e) {
      setError(e.response?.data?.detail || e.message || "Unknown error");
    } finally {
      clearInterval(ticker);
      setStep("");
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">

      {/* ── Header ── */}
      <header className="bg-brand shadow-md">
        <div className="max-w-screen-2xl mx-auto px-6 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-white tracking-tight">
              ⚖️ BRAHMO Citation Safety Engine
            </h1>
            <p className="text-blue-200 text-xs mt-0.5">
              Make AI Safe for Lawyers — Citation Verification + Section Normalizer
            </p>
          </div>
          <StatusBar health={health} />
        </div>
      </header>

      {/* ── Main layout: left content + right notes panel ── */}
      <div className="max-w-screen-2xl mx-auto px-6 py-6 flex-1 flex gap-6 w-full">

        {/* Left — main content */}
        <div className="flex-1 flex flex-col gap-6 min-w-0">

          {/* Matter selector */}
          <MatterSelector
            matters={matters}
            selected={selected}
            onSelect={setSelected}
            query={query}
            onQueryChange={setQuery}
          />

          {/* Action button */}
          <button
            onClick={handleCompare}
            disabled={loading || !query.trim()}
            className="w-full bg-brand hover:bg-brand-light disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold py-3 px-6 rounded-xl transition-colors shadow"
          >
            {loading ? "⏳ Running pipeline…" : "⚖️ Ask with Citation Verification"}
          </button>

          {/* Loading state */}
          {loading && (
            <div className="bg-blue-50 border border-blue-200 rounded-xl px-6 py-4 flex items-center gap-3">
              <div className="animate-spin h-5 w-5 border-2 border-brand border-t-transparent rounded-full" />
              <div>
                <p className="text-sm font-medium text-blue-900">{step}</p>
                <p className="text-xs text-blue-600 mt-0.5">
                  Extraction → Pre-filter → IK Verification → Annotation
                </p>
              </div>
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-xl px-6 py-4">
              <p className="text-sm font-semibold text-red-800">❌ Error</p>
              <p className="text-sm text-red-700 mt-1 font-mono">{error}</p>
            </div>
          )}

          {/* Results */}
          {result && !loading && (
            <>
              {/* Side-by-side panels */}
              <div className="grid grid-cols-2 gap-4" style={{ minHeight: "480px" }}>
                <ResponsePanel
                  title="🤖 Generic Gemini — No Verification"
                  content={result.generic}
                  isEnhanced={false}
                />
                <ResponsePanel
                  title="🛡️ BRAHMO System — Citation Verified"
                  content={result.enhanced}
                  isEnhanced={true}
                />
              </div>

              {/* Report — passes onCopyToNotes down */}
              <VerificationReport
                report={result.report}
                onCopyToNotes={addNote}
              />

              {/* Summary */}
              <SummaryCallout report={result.report} />
            </>
          )}
        </div>

        {/* Right — session notes panel (fixed width, full height) */}
        <div className="w-80 flex-shrink-0 flex flex-col" style={{ minHeight: "calc(100vh - 120px)" }}>
          <div className="sticky top-6 flex flex-col" style={{ height: "calc(100vh - 120px)" }}>
            <SessionNotes
              notes={notes}
              onAdd={addNote}
              onClear={clearNotes}
            />
          </div>
        </div>

      </div>
    </div>
  );
}

function SummaryCallout({ report }) {
  const { total, verified, removed, unverified, accuracy_pct, section_alerts } = report;
  if (total === 0 && section_alerts.length === 0) return null;

  return (
    <div className="rounded-xl border border-gray-200 bg-white shadow-sm p-4 text-sm">
      <p className="font-semibold text-gray-700 mb-2">📊 Pipeline Summary</p>
      <div className="flex flex-wrap gap-3 text-xs">
        {total > 0 && (
          <span className="bg-gray-100 px-3 py-1 rounded-full">
            {total} citation{total !== 1 ? "s" : ""} scanned
          </span>
        )}
        {verified > 0 && (
          <span className="bg-green-100 text-green-800 px-3 py-1 rounded-full font-medium">
            {verified} confirmed real ✅
          </span>
        )}
        {removed > 0 && (
          <span className="bg-red-100 text-red-800 px-3 py-1 rounded-full font-medium">
            {removed} hallucinated — blocked ❌
          </span>
        )}
        {unverified > 0 && (
          <span className="bg-yellow-100 text-yellow-800 px-3 py-1 rounded-full font-medium">
            {unverified} unverified ⚠️
          </span>
        )}
        {section_alerts.length > 0 && (
          <span className="bg-amber-100 text-amber-800 px-3 py-1 rounded-full font-medium">
            {section_alerts.length} old law section{section_alerts.length !== 1 ? "s" : ""} converted ⚠️
          </span>
        )}
        {total > 0 && (
          <span className={`px-3 py-1 rounded-full font-bold ${
            accuracy_pct === 100
              ? "bg-green-100 text-green-800"
              : accuracy_pct >= 70
              ? "bg-yellow-100 text-yellow-800"
              : "bg-red-100 text-red-800"
          }`}>
            {accuracy_pct}% accuracy
          </span>
        )}
      </div>
    </div>
  );
}
