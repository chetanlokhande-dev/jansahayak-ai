import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { api } from '../lib/api';
import { ErrorBanner, PageTitle, Spinner } from '../components/Feedback';

const fmt = (iso) => { try { return new Date(iso).toLocaleString(); } catch { return iso; } };

export default function History() {
  const { t } = useApp();
  const [data, setData] = useState(null);
  const [error, setError] = useState('');

  const load = useCallback(() => {
    api.history().then((d) => { setData(d); setError(''); }).catch((e) => setError(e.message));
  }, []);
  useEffect(load, [load]);

  const act = (fn) => fn().then(load).catch((e) => setError(e.message));
  const empty = data && !data.conversations.length && !data.documents.length;

  return (
    <div className="mx-auto max-w-3xl">
      <PageTitle title={t('history.title')} subtitle={t('history.subtitle')} />
      <ErrorBanner message={error} onRetry={load} />
      {!data && !error && <Spinner />}
      {empty && <p className="text-slate-600">{t('history.empty')}</p>}

      {data && data.conversations.length > 0 && (
        <section className="mb-6">
          <h2 className="mb-2 text-lg font-semibold text-brand-800">{t('history.chats')}</h2>
          <ul className="space-y-2">
            {data.conversations.map((c) => (
              <li key={c.id} className="card flex flex-wrap items-center justify-between gap-2 p-4">
                <div className="min-w-0">
                  <p className="truncate font-medium">{c.title}</p>
                  <p className="text-sm text-slate-500">{fmt(c.updated_at)}</p>
                </div>
                <div className="flex gap-2">
                  <Link to={`/assistant?c=${c.id}`} className="btn-secondary !min-h-[40px]">{t('common.open')}</Link>
                  <button type="button" className="btn !min-h-[40px] border border-red-200 text-red-700 hover:bg-red-50" onClick={() => act(() => api.deleteConversation(c.id))}>{t('common.delete')}</button>
                </div>
              </li>
            ))}
          </ul>
        </section>
      )}

      {data && data.documents.length > 0 && (
        <section className="mb-6">
          <h2 className="mb-2 text-lg font-semibold text-brand-800">{t('history.docs')}</h2>
          <ul className="space-y-2">
            {data.documents.map((d) => (
              <li key={d.id} className="card flex flex-wrap items-center justify-between gap-2 p-4">
                <div className="min-w-0">
                  <p className="truncate font-medium">📄 {d.filename}</p>
                  <p className="text-sm text-slate-500">{fmt(d.created_at)} · {d.kind.toUpperCase()}</p>
                </div>
                <div className="flex gap-2">
                  <Link to={`/assistant?doc=${d.id}`} className="btn-secondary !min-h-[40px]">{t('common.askAI')}</Link>
                  <button type="button" className="btn !min-h-[40px] border border-red-200 text-red-700 hover:bg-red-50" onClick={() => act(() => api.deleteDocument(d.id))}>{t('common.delete')}</button>
                </div>
              </li>
            ))}
          </ul>
        </section>
      )}

      {data && !empty && (
        <button type="button" className="btn border border-red-300 text-red-700 hover:bg-red-50"
                onClick={() => { if (window.confirm(t('history.confirm'))) act(() => api.clearHistory()); }}>
          {t('history.clear')}
        </button>
      )}
    </div>
  );
}
