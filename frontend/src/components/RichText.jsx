// Renders the small markdown subset the assistant uses (bold, bullets, headings, italics)
// as React elements. Never uses dangerouslySetInnerHTML, so model output cannot inject HTML.
function inline(text, keyPrefix) {
  const parts = [];
  const re = /(\*\*[^*]+\*\*|_[^_]+_)/g;
  let last = 0;
  let m;
  let i = 0;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) parts.push(text.slice(last, m.index));
    const token = m[0];
    parts.push(
      token.startsWith('**')
        ? <strong key={`${keyPrefix}-${i++}`}>{token.slice(2, -2)}</strong>
        : <em key={`${keyPrefix}-${i++}`}>{token.slice(1, -1)}</em>,
    );
    last = m.index + token.length;
  }
  if (last < text.length) parts.push(text.slice(last));
  return parts;
}

export default function RichText({ text, className = '' }) {
  const lines = String(text || '').replace(/\r/g, '').split('\n');
  const blocks = [];
  let list = [];
  const flush = () => {
    if (list.length) {
      blocks.push(
        <ul key={`ul-${blocks.length}`} className="my-2 list-disc space-y-1 pl-6">
          {list.map((item, i) => <li key={i}>{inline(item, `li${blocks.length}-${i}`)}</li>)}
        </ul>,
      );
      list = [];
    }
  };
  lines.forEach((raw, idx) => {
    const line = raw.trim();
    if (/^[-*•]\s+/.test(line)) { list.push(line.replace(/^[-*•]\s+/, '')); return; }
    flush();
    if (!line) return;
    if (/^#+\s/.test(line)) {
      blocks.push(<h4 key={idx} className="mt-3 font-semibold text-brand-800">{inline(line.replace(/^#+\s*/, ''), `h${idx}`)}</h4>);
    } else {
      blocks.push(<p key={idx} className="my-2 leading-relaxed">{inline(line, `p${idx}`)}</p>);
    }
  });
  flush();
  return <div className={className}>{blocks}</div>;
}
