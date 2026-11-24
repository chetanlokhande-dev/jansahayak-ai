import { useApp } from '../context/AppContext';
import { PageTitle } from '../components/Feedback';

export default function About() {
  const { t, meta } = useApp();
  return (
    <div className="mx-auto max-w-3xl space-y-5">
      <PageTitle title={t('about.title')} subtitle={t('tagline')} />

      <section className="card p-5">
        <h2 className="text-lg font-semibold text-brand-800">{t('about.what')}</h2>
        <p className="mt-2 leading-relaxed">{t('about.whatText')}</p>
        {meta && (
          <p className="mt-3 inline-block rounded-lg bg-brand-50 px-3 py-1 text-sm text-brand-800">
            {t(`about.mode.${meta.ai_mode}`)}
          </p>
        )}
      </section>

      <section className="card border-amber-200 bg-amber-50 p-5">
        <h2 className="text-lg font-semibold text-amber-900">{t('about.limits')}</h2>
        <ul className="mt-2 list-disc space-y-1 pl-6">
          {['l1', 'l2', 'l3', 'l4', 'l5'].map((k) => <li key={k}>{t(`about.${k}`)}</li>)}
        </ul>
      </section>

      <section className="card p-5">
        <h2 className="text-lg font-semibold text-brand-800">{t('about.sources')}</h2>
        <ul className="mt-2 space-y-1">
          {(meta ? meta.official_portals : []).map((p) => (
            <li key={p.url}><a className="text-brand-700 underline" href={p.url} target="_blank" rel="noopener noreferrer">{p.title} ↗</a></li>
          ))}
        </ul>
      </section>

      <section className="card p-5">
        <h2 className="text-lg font-semibold text-brand-800">{t('about.privacy')}</h2>
        <p className="mt-2 leading-relaxed">{t('about.p1')}</p>
      </section>
    </div>
  );
}
