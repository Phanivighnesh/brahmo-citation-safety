import { useState, useRef, useEffect } from "react";

export default function SessionNotes({ notes, onAdd, onClear }) {
  const [input, setInput] = useState("");
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [notes]);

  function handleAdd() {
    const trimmed = input.trim();
    if (!trimmed) return;
    onAdd({ text: trimmed, time: new Date().toLocaleTimeString(), type: "manual" });
    setInput("");
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleAdd();
    }
  }

  return (
    <div className="flex flex-col h-full rounded-xl border border-gray-200 bg-white shadow-sm overflow-hidden">

      {/* Header — matches VerificationReport header style */}
      <div className="flex items-center justify-between bg-gray-800 px-4 py-2">
        <div>
          <h3 className="text-white font-semibold text-sm">📝 Lawyer's Session Notes</h3>
          <p className="text-gray-400 text-xs">Persists across queries · Resets on page refresh</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-gray-400 text-xs">
            {notes.length} note{notes.length !== 1 ? "s" : ""}
          </span>
          {notes.length > 0 && (
            <button
              onClick={onClear}
              className="text-xs bg-gray-700 hover:bg-gray-600 text-gray-200 px-2 py-0.5 rounded transition-colors"
            >
              Clear all
            </button>
          )}
        </div>
      </div>

      {/* Notes list */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2 min-h-0 bg-gray-50">
        {notes.length === 0 ? (
          <div className="text-center text-gray-400 text-xs mt-8">
            <p className="text-2xl mb-2">📋</p>
            <p>No notes yet.</p>
            <p className="mt-1">Type below or click <span className="font-medium text-gray-500">📝 Notes</span></p>
            <p>on any verified citation.</p>
          </div>
        ) : (
          notes.map((note, i) => (
            <NoteEntry key={i} note={note} />
          ))
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input — matches MatterSelector textarea style */}
      <div className="border-t border-gray-200 p-3 bg-white">
        <div className="flex gap-2">
          <textarea
            rows={2}
            className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand resize-none"
            placeholder="Type a note… (Enter to save)"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
          />
          <button
            onClick={handleAdd}
            disabled={!input.trim()}
            className="bg-brand hover:bg-brand-light disabled:opacity-40 disabled:cursor-not-allowed text-white text-xs font-semibold px-3 rounded-lg transition-colors"
          >
            Save
          </button>
        </div>
      </div>
    </div>
  );
}

function NoteEntry({ note }) {
  const isCitation = note.type === "citation";

  return (
    <div className={`rounded-lg px-3 py-2 text-xs border ${
      isCitation
        ? "bg-green-50 border-green-200"
        : "bg-white border-gray-200"
    }`}>
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          {isCitation && (
            <p className="font-semibold text-green-700 mb-0.5">✅ Citation saved</p>
          )}
          <p className="text-gray-800 break-words whitespace-pre-wrap">{note.text}</p>
        </div>
        <span className="text-gray-400 whitespace-nowrap text-[10px] mt-0.5">{note.time}</span>
      </div>
    </div>
  );
}
