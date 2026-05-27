export default function StatusBar({ health }) {
  if (!health) return null;

  const dot = (ok) => (
    <span className={`inline-block w-2 h-2 rounded-full mr-1 ${ok ? "bg-green-400" : "bg-red-400"}`} />
  );

  return (
    <div className="flex items-center gap-4 text-xs text-gray-400">
      <span>{dot(health.gemini_key)} Gemini</span>
      <span>{dot(health.ik_key)} Indian Kanoon</span>
      <span className="text-gray-300">|</span>
      <span className="font-mono">{health.model}</span>
    </div>
  );
}
