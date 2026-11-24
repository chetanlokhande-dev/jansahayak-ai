import { useApp } from '../context/AppContext';

export default function SourceList({ sources }) {
  const { t } = useApp();
  if (!sources || !sources.length) return null;
  return (
    <div className="mt-4 rounded-xl bg-slate-50 p-3">
      <h4 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-500">{t('common.sources')}</h4>
      <ul className="space-y-2">
        {sources.map((s) => (
          <li key={s.id} className="flex flex-wrap items-center gap-2 text-sm">
            <span className="chip bg-brand-100 text-brand-800">{s.id}</span>
            {s.url ? (
              <a href={s.url} target="_blank" rel="noopener noreferrer" className="font-medium text-brand-700 underline">
                {s.title} ↗
              </a>
            ) : (
              <span className="font-medium">{s.title}</span>
            )}
            {s.kind === 'uploaded' && <span className="chip bg-leaf-100 text-leaf-700">{t('common.yourDoc')}</span>}
            {s.section && <span className="text-slate-500">· {s.section}</span>}
            {s.data_status === 'sample' && <span className="chip bg-amber-100 text-amber-800">{t('common.sample')}</span>}
          </li>
        ))}
      </ul>
    </div>
  );
}
