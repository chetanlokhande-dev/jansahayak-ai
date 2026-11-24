import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { api } from '../lib/api';
import { ErrorBanner, PageTitle, Spinner } from '../components/Feedback';

const List = ({ title, items }) => (
  <div className="mt-3">
    <h4 className="font-semibold text-brand-800">{title}</h4>
    <ul className="list-disc space-y-1 pl-6">{items.map((i, n) => <li key={n}>{i}</li>)}</ul>
  </div>
);

export default function SchemeFinder() {
  const { t } = useApp();
  const [q, setQ] = useState('');
  const [category, setCategory] = useState('');
  const [data, setData] = useState(null);
  const [open, setOpen] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    const timer = setTimeout(() => {
      api.schemes(q, category).then((d) => { setData(d); setError(''); }).catch((e) => setError(e.message)).finally(() => setLoading(false));
    }, 250);
    return () => clearTimeout(timer);
  }, [q, category]);

  return (
    <div>
      <PageTitle title={t('schemes.title')} subtitle={t('schemes.subtitle')} />
      <div className="flex flex-col gap-3 sm:flex-row">
        <input className="input sm:max-w-md" value={q} onChange={(e) => setQ(e.target.value)} placeholder={t('schemes.search')} aria-label={t('schemes.search')} />
      </div>
      {data && (
        <div className="mt-3 flex flex-wrap gap-2" role="group" aria-label="Category">
          {['', ...data.categories].map((c) => (
            <button key={c || 'all'} type="button" onClick={() => setCategory(c)} aria-pressed={category === c}
              className={`chip border ${category === c ? 'border-brand-600 bg-brand-600 text-white' : 'border-brand-200 bg-white text-brand-700 hover:bg-brand-50'}`}>
              {c ? c.replace(/-/g, ' ') : t('schemes.all')}
            </button>
          ))}
        </div>
      )}
      {data && <p className="mt-3 rounded-lg bg-amber-50 p-2 text-sm text-amber-900">⚠️ {data.data_status.label}. {data.data_status.disclaimer}</p>}

      <div className="mt-4 space-y-4">
        {loading && !data && <Spinner />}
        <ErrorBanner message={error} />
        {data && data.schemes.length === 0 && <p className="text-slate-600">{t('schemes.none')}</p>}
        {data && data.schemes.map((s) => {
          const isOpen = open === s.id;
          return (
            <article key={s.id} className="card p-5">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div>
                  <span className="chip mb-2 bg-leaf-100 capitalize text-leaf-700">{s.category.replace(/-/g, ' ')}</span>
                  <h2 className="text-xl font-bold text-brand-800">{s.name}</h2>
                  <p className="mt-1 text-slate-600">{s.summary}</p>
                </div>
                <button type="button" aria-expanded={isOpen} onClick={() => setOpen(isOpen ? null : s.id)} className="btn-secondary !min-h-[44px]">
                  {isOpen ? t('common.close') : t('common.view')}
                </button>
              </div>
              {isOpen && (
                <div className="mt-3 border-t border-slate-100 pt-3">
                  <p className="text-sm text-slate-500">{s.ministry}</p>
                  <List title={t('schemes.benefits')} items={s.benefits} />
                  <List title={t('schemes.who')} items={s.eligibility_text} />
                  <List title={t('schemes.docs')} items={s.required_documents} />
                  <List title={t('schemes.apply')} items={s.how_to_apply} />
                  <div className="mt-4 flex flex-wrap gap-3">
                    <a href={s.official_url} target="_blank" rel="noopener noreferrer" className="btn-primary">{t('schemes.visit')} ↗</a>
                    <Link to="/eligibility" className="btn-secondary">{t('schemes.check')}</Link>
                    <Link to={`/assistant?q=${encodeURIComponent(s.name)}`} className="btn-secondary">{t('common.askAI')}</Link>
                  </div>
                </div>
              )}
            </article>
          );
        })}
      </div>
    </div>
  );
}
