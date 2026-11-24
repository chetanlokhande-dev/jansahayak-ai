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

export default function RightsExplorer() {
  const { t } = useApp();
  const [data, setData] = useState(null);
  const [open, setOpen] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => { api.rights().then(setData).catch((e) => setError(e.message)); }, []);

  return (
    <div>
      <PageTitle title={t('rights.title')} subtitle={t('rights.subtitle')} />
      <ErrorBanner message={error} />
      {!data && !error && <Spinner />}
      {data && <p className="mb-4 rounded-lg bg-amber-50 p-2 text-sm text-amber-900">⚠️ {data.data_status.label}. {data.data_status.disclaimer}</p>}
      <div className="grid gap-4 md:grid-cols-2">
        {data && data.rights.map((r) => {
          const isOpen = open === r.id;
          return (
            <article key={r.id} className="card p-5">
              <span className="chip mb-2 bg-brand-100 capitalize text-brand-800">{r.category}</span>
              <h2 className="text-xl font-bold text-brand-800">{r.title}</h2>
              <p className="mt-1 text-slate-600">{r.summary}</p>
              <button type="button" aria-expanded={isOpen} onClick={() => setOpen(isOpen ? null : r.id)} className="btn-secondary mt-3 !min-h-[44px]">
                {isOpen ? t('common.close') : t('common.view')}
              </button>
              {isOpen && (
                <div className="mt-3 border-t border-slate-100 pt-3">
                  <List title={t('rights.points')} items={r.key_points} />
                  <List title={t('rights.todo')} items={r.what_to_do} />
                  <p className="mt-3 text-sm text-slate-500">{t('rights.law')}: {r.law}</p>
                  <div className="mt-3 flex flex-wrap gap-3">
                    <a href={r.official_url} target="_blank" rel="noopener noreferrer" className="btn-primary">{t('common.official')} ↗</a>
                    <Link to={`/assistant?q=${encodeURIComponent(r.title)}`} className="btn-secondary">{t('common.askAI')}</Link>
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
