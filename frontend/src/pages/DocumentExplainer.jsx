import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { api } from '../lib/api';
import { ListenButton } from '../components/VoiceControls';
import { ErrorBanner, Notice, PageTitle, Spinner } from '../components/Feedback';

const ACCEPT = '.pdf,.docx,.txt,.png,.jpg,.jpeg,.webp,.tif,.tiff,.bmp';

function Section({ title, items }) {
  if (!items || !items.length) return null;
  return (
    <section className="mt-5">
      <h3 className="mb-1 text-lg font-semibold text-brand-800">{title}</h3>
      <ul className="list-disc space-y-1 pl-6">{items.map((i, n) => <li key={n}>{i}</li>)}</ul>
    </section>
  );
}

export default function DocumentExplainer() {
  const { lang, t } = useApp();
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [dragging, setDragging] = useState(false);
  const [samples, setSamples] = useState([]);
  const inputRef = useRef(null);

  useEffect(() => { api.sampleDocuments().then((r) => setSamples(r.documents)).catch(() => {}); }, []);

  const run = async (fn) => {
    setError(''); setResult(null); setLoading(true);
    try { setResult(await fn()); } catch (e) { setError(e.message); } finally { setLoading(false); }
  };
  const upload = (file) => file && run(() => api.uploadDocument(file, lang));

  const a = result && result.analysis;
  const spoken = a ? [a.summary, ...(a.key_points || []), ...(a.next_steps || [])].join('. ') : '';

  return (
    <div className="mx-auto max-w-3xl">
      <PageTitle title={t('docs.title')} subtitle={t('docs.subtitle')} />

      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => { e.preventDefault(); setDragging(false); upload(e.dataTransfer.files[0]); }}
        className={`card flex flex-col items-center gap-3 border-2 border-dashed p-8 text-center transition ${dragging ? 'border-brand-500 bg-brand-50' : 'border-brand-200'}`}
      >
        <span aria-hidden className="text-4xl">📄</span>
        <p className="text-lg font-semibold text-brand-800">{t('docs.drop')}</p>
        <p className="text-slate-500">{t('docs.types')}</p>
        <input ref={inputRef} type="file" accept={ACCEPT} className="sr-only" aria-label={t('docs.browse')}
               onChange={(e) => { upload(e.target.files[0]); e.target.value = ''; }} />
        <button type="button" onClick={() => inputRef.current.click()} className="btn-primary" disabled={loading}>{t('docs.browse')}</button>
      </div>

      {samples.length > 0 && (
        <div className="mt-3 flex flex-wrap items-center gap-2 text-sm">
          <span className="text-slate-500">{t('docs.samples')}:</span>
          {samples.map((s) => (
            <button key={s} type="button" disabled={loading} onClick={() => run(() => api.analyzeSample(s, lang))} className="chip border border-brand-200 bg-white text-brand-700 hover:bg-brand-50">
              {s.replace(/^SAMPLE_/, '').replace(/\.txt$/, '').replace(/_/g, ' ')}
            </button>
          ))}
        </div>
      )}

      <div className="mt-5 space-y-4" aria-live="polite">
        {loading && <div className="card p-4"><Spinner label={t('docs.analyzing')} /></div>}
        <ErrorBanner message={error} />
        {result && (
          <article className="card p-5">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h2 className="break-all text-xl font-bold text-brand-800">{result.document.filename}</h2>
              <ListenButton text={spoken} />
            </div>
            <Notice>{result.notice}</Notice>
            {result.document.warnings.map((w, i) => <div key={i} className="mt-2"><Notice>{w}</Notice></div>)}
            <section className="mt-4 rounded-xl bg-brand-50 p-4">
              <h3 className="mb-1 text-lg font-semibold text-brand-800">{t('docs.summary')}</h3>
              <p className="leading-relaxed">{a.summary || '—'}</p>
            </section>
            <Section title={t('docs.keyPoints')} items={a.key_points} />
            <Section title={t('docs.benefits')} items={a.benefits} />
            <Section title={t('docs.required')} items={a.required_documents} />
            <Section title={t('docs.dates')} items={a.important_dates_amounts} />
            <Section title={t('docs.steps')} items={a.next_steps} />
            <Section title={t('docs.unclear')} items={a.unclear} />
            <Link to={`/assistant?doc=${result.document.id}`} className="btn-green mt-6">💬 {t('docs.ask')}</Link>
          </article>
        )}
      </div>
    </div>
  );
}
