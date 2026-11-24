import { useEffect, useState } from 'react';
import { useApp } from '../context/AppContext';
import { api } from '../lib/api';
import RichText from '../components/RichText';
import { ListenButton } from '../components/VoiceControls';
import { ErrorBanner, PageTitle, Spinner } from '../components/Feedback';

const STATUS_STYLE = {
  likely_eligible: ['elig.likely', 'border-leaf-200 bg-leaf-50', 'bg-leaf-600 text-white'],
  needs_more_info: ['elig.need', 'border-amber-200 bg-amber-50', 'bg-amber-500 text-white'],
  not_eligible: ['elig.not', 'border-slate-200 bg-white', 'bg-slate-500 text-white'],
};
const STATE_ICON = { met: '✔', not_met: '✘', unknown: '?' };
const STATE_KEY = { met: 'elig.met', not_met: 'elig.notMet', unknown: 'elig.unknown' };

export default function EligibilityChecker() {
  const { lang, t } = useApp();
  const [fields, setFields] = useState([]);
  const [answers, setAnswers] = useState({});
  const [step, setStep] = useState(-1); // -1 = intro
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    api.eligibilityFields(lang).then((r) => setFields(r.fields)).catch((e) => setError(e.message));
  }, [lang]);

  const field = fields[step];
  const setAnswer = (id, value) => setAnswers((a) => {
    const next = { ...a };
    if (value === null || value === '') delete next[id]; else next[id] = value;
    return next;
  });

  const submit = async (finalAnswers) => {
    setLoading(true); setError('');
    try { setResult(await api.checkEligibility(finalAnswers, lang)); } catch (e) { setError(e.message); } finally { setLoading(false); }
  };
  const advance = (answersNow = answers) => {
    if (step + 1 >= fields.length) { setStep(fields.length); submit(answersNow); } else setStep(step + 1);
  };
  const choose = (value) => { const next = { ...answers }; if (value === null) delete next[field.id]; else next[field.id] = value; setAnswers(next); advance(next); };
  const restart = () => { setAnswers({}); setResult(null); setStep(-1); setError(''); };

  const progress = fields.length ? Math.max(0, Math.min(step, fields.length)) / fields.length : 0;

  return (
    <div className="mx-auto max-w-3xl">
      <PageTitle title={t('elig.title')} subtitle={t('elig.subtitle')} />
      <ErrorBanner message={error} />

      {step === -1 && !result && (
        <div className="card space-y-4 p-6">
          <p className="leading-relaxed">{t('elig.intro')}</p>
          <button type="button" className="btn-primary" disabled={!fields.length} onClick={() => setStep(0)}>{t('elig.start')}</button>
        </div>
      )}

      {field && !result && !loading && (
        <div className="card p-6">
          <div className="mb-4 h-2 overflow-hidden rounded-full bg-brand-100" role="progressbar" aria-valuemin={0} aria-valuemax={fields.length} aria-valuenow={step}>
            <div className="h-full bg-leaf-600 transition-all" style={{ width: `${progress * 100}%` }} />
          </div>
          <p className="text-sm text-slate-500">{t('elig.step')} {step + 1} / {fields.length}</p>
          <h2 className="mt-1 text-xl font-semibold text-brand-800">{field.label}</h2>

          <div className="mt-5">
            {field.type === 'number' && (
              <form onSubmit={(e) => { e.preventDefault(); advance(); }} className="flex flex-col gap-3 sm:flex-row">
                <input type="number" inputMode="numeric" min={field.min} max={field.max} className="input sm:max-w-[200px]"
                       value={answers[field.id] ?? ''} onChange={(e) => setAnswer(field.id, e.target.value === '' ? null : Number(e.target.value))}
                       aria-label={t('elig.number')} placeholder={t('elig.number')} autoFocus />
                <button type="submit" className="btn-primary">{t('common.next')}</button>
              </form>
            )}
            {(field.type === 'bool' || field.type === 'choice') && (
              <div className="grid gap-3 sm:grid-cols-3">
                {field.options.map((o) => (
                  <button key={o.value} type="button" onClick={() => choose(field.type === 'bool' ? o.value === 'true' : o.value)}
                          className="btn-secondary !min-h-[56px] text-lg">{o.label}</button>
                ))}
                <button type="button" onClick={() => choose(null)} className="btn border border-slate-300 bg-white !min-h-[56px] text-lg text-slate-600 hover:bg-slate-50">{t('elig.notSure')}</button>
              </div>
            )}
          </div>

          <div className="mt-6 flex justify-between">
            <button type="button" className="btn-secondary !min-h-[40px]" onClick={() => setStep(step - 1)} disabled={step === 0}>{t('common.back')}</button>
            {field.type === 'number' && <button type="button" className="text-brand-700 underline" onClick={() => { setAnswer(field.id, null); advance({ ...answers, [field.id]: undefined }); }}>{t('elig.skip')}</button>}
          </div>
        </div>
      )}

      {loading && <div className="card p-4"><Spinner label={t('elig.checking')} /></div>}

      {result && (
        <div className="space-y-4">
          {result.explanation && (
            <div className="card border-brand-200 bg-brand-50 p-5">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h2 className="text-lg font-semibold text-brand-800">{t('elig.explain')}</h2>
                <ListenButton text={result.explanation} />
              </div>
              <RichText text={result.explanation} />
            </div>
          )}
          {result.results.map((r) => {
            const [labelKey, boxStyle, badgeStyle] = STATUS_STYLE[r.status];
            return (
              <article key={r.scheme_id} className={`rounded-2xl border p-5 shadow-card ${boxStyle}`}>
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <h3 className="text-lg font-bold text-brand-800">{r.scheme_name}</h3>
                  <span className={`chip ${badgeStyle}`}>{t(labelKey)}</span>
                </div>
                <p className="mt-1 text-slate-700">{r.summary}</p>
                <details className="mt-2">
                  <summary className="cursor-pointer font-medium text-brand-700">{t('elig.why')}</summary>
                  <ul className="mt-2 space-y-1">
                    {r.criteria.map((c, i) => (
                      <li key={i} className="flex gap-2">
                        <span aria-hidden className={c.state === 'met' ? 'text-leaf-600' : c.state === 'not_met' ? 'text-red-600' : 'text-amber-600'}>{STATE_ICON[c.state]}</span>
                        <span>{c.label} <span className="text-sm text-slate-500">({t(STATE_KEY[c.state])})</span></span>
                      </li>
                    ))}
                  </ul>
                </details>
                <a href={r.official_url} target="_blank" rel="noopener noreferrer" className="mt-3 inline-block font-medium text-brand-700 underline">{t('common.official')}: {r.source_name} ↗</a>
              </article>
            );
          })}
          <p className="rounded-xl bg-slate-100 p-3 text-sm text-slate-600">{result.disclaimer}</p>
          <button type="button" onClick={restart} className="btn-secondary">{t('elig.restart')}</button>
        </div>
      )}
    </div>
  );
}
