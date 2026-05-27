// Strip HTML tags from IK case names embedded in annotated text
function stripHtml(str) {
  return str.replace(/<[^>]*>/g, "").replace(/\s+/g, " ");
}

export default function ResponsePanel({ title, content, isEnhanced = false }) {
  if (!content) return null;

  // Clean HTML tags from IK titles before rendering
  const cleanContent = stripHtml(content);

  return (
    <div className="flex flex-col h-full">
      <div className={`px-4 py-2 rounded-t-xl font-semibold text-sm ${
        isEnhanced ? "bg-brand text-white" : "bg-gray-700 text-white"
      }`}>
        {title}
      </div>
      <div className="flex-1 overflow-y-auto bg-white border border-gray-200 rounded-b-xl p-4 text-sm leading-relaxed whitespace-pre-wrap font-mono">
        {isEnhanced
          ? <AnnotatedText content={cleanContent} />
          : <span className="text-gray-800">{cleanContent}</span>
        }
      </div>
    </div>
  );
}

function AnnotatedText({ content }) {
  // Split on badge markers and colour each badge inline
  const parts = content.split(
    /(✅ VERIFIED[^\n]*|⚠️ UNVERIFIED[^\n]*|❌ REMOVED[^\n]*|⚠️ CORRECTED[^\n]*)/g
  );

  return (
    <>
      {parts.map((part, i) => {
        if (part.startsWith("✅ VERIFIED")) {
          return (
            <span key={i} className="inline-block bg-green-100 text-green-800 text-xs px-1.5 py-0.5 rounded font-sans font-medium mx-0.5 border border-green-300">
              {part}
            </span>
          );
        }
        if (part.startsWith("❌ REMOVED")) {
          return (
            <span key={i} className="inline-block bg-red-100 text-red-800 text-xs px-1.5 py-0.5 rounded font-sans font-medium mx-0.5 border border-red-300">
              {part}
            </span>
          );
        }
        if (part.startsWith("⚠️ UNVERIFIED")) {
          return (
            <span key={i} className="inline-block bg-yellow-100 text-yellow-800 text-xs px-1.5 py-0.5 rounded font-sans font-medium mx-0.5 border border-yellow-300">
              {part}
            </span>
          );
        }
        if (part.startsWith("⚠️ CORRECTED")) {
          return (
            <span key={i} className="inline-block bg-blue-100 text-blue-800 text-xs px-1.5 py-0.5 rounded font-sans font-medium mx-0.5 border border-blue-300">
              {part}
            </span>
          );
        }
        return <span key={i} className="text-gray-800">{part}</span>;
      })}
    </>
  );
}
