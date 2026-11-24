import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { MicButton } from '../components/VoiceControls';

const ACTIONS = [
  ['/assistant', 'home.a1', 'home.a1d', '💬'],
  ['/documents', 'home.a2', 'home.a2d', '📄'],
  ['/eligibility', 'home.a3', 'home.a3d', '✅'],
  ['/rights', 'home.a4', 'home.a4d', '⚖️'],
  ['/schemes', 'home.a5', 'home.a5d', '🔎'],
];

export default function Home() {
  const { t } = useApp();
  const navigate = useNavigate();
  const [q, setQ] = useState('');

  const go = (text) => {
    const query = (text ?? q).trim();
    navigate(query ? `/assistant?q=${encodeURIComponent(query)}` : '/assistant');
  };

  return (
    <div className="space-y-8">
      <section className="rounded-3xl bg-gradient-to-br from-brand-700 to-brand-600 p-6 text-white shadow-card sm:p-10">
        <h1 className="max-w-3xl text-3xl font-bold leading-tight sm:text-4xl">{t('home.title')}</h1>
        <p className="mt-3 max-w-2xl text-lg text-brand-100">{t('home.subtitle')}</p>
        <form
          onSubmit={(e) => { e.preventDefault(); go(); }}
          className="mt-6 flex max-w-3xl flex-col gap-3 sm:flex-row"
          role="search"
        >
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder={t('home.search')}
            aria-label={t('home.search')}
            className="input flex-1 !border-transparent text-slate-900"
          />
          <div className="flex gap-3">
            <MicButton onText={(text) => { setQ(text); }} />
            <button type="submit" className="btn-green flex-1 sm:flex-none">{t('home.ask')}</button>
          </div>
        </form>
        <div className="mt-4 flex flex-wrap items-center gap-2">
          <span className="text-sm text-brand-100">{t('home.try')}:</span>
          {['home.q1', 'home.q2', 'home.q3'].map((k) => (
            <button key={k} type="button" onClick={() => go(t(k))} className="chip bg-white/15 text-white hover:bg-white/25">
              {t(k)}
            </button>
          ))}
        </div>
      </section>

      <section aria-label="Actions" className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {ACTIONS.map(([to, title, desc, icon]) => (
          <Link key={to} to={to} className="card flex items-start gap-4 p-5 transition hover:-translate-y-0.5 hover:border-brand-200">
            <span aria-hidden className="grid h-12 w-12 shrink-0 place-items-center rounded-xl bg-leaf-50 text-2xl">{icon}</span>
            <span>
              <span className="block text-lg font-semibold text-brand-800">{t(title)}</span>
              <span className="block text-slate-600">{t(desc)}</span>
            </span>
          </Link>
        ))}
      </section>
    </div>
  );
}
