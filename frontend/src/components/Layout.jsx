import { NavLink, Outlet, Link } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { LANGS } from '../lib/i18n';

const NAV = [
  ['/', 'nav.home', '🏠'],
  ['/assistant', 'nav.assistant', '💬'],
  ['/documents', 'nav.documents', '📄'],
  ['/schemes', 'nav.schemes', '🔎'],
  ['/eligibility', 'nav.eligibility', '✅'],
  ['/rights', 'nav.rights', '⚖️'],
  ['/history', 'nav.history', '🕘'],
  ['/about', 'nav.about', 'ℹ️'],
];

function LanguageSelector() {
  const { lang, setLang, t } = useApp();
  return (
    <div role="group" aria-label={t('lang.label')} className="flex rounded-xl bg-brand-50 p-1">
      {LANGS.map((l) => (
        <button
          key={l.code}
          type="button"
          onClick={() => setLang(l.code)}
          aria-pressed={lang === l.code}
          className={`min-h-[44px] min-w-[64px] rounded-lg px-3 text-base font-semibold transition ${
            lang === l.code ? 'bg-brand-600 text-white shadow' : 'text-brand-700 hover:bg-brand-100'
          }`}
        >
          {l.native}
        </button>
      ))}
    </div>
  );
}

export default function Layout() {
  const { t } = useApp();
  return (
    <div className="flex min-h-screen flex-col">
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:left-2 focus:top-2 focus:z-50 focus:rounded focus:bg-white focus:p-3">
        Skip to content
      </a>
      <header className="border-b border-brand-100 bg-white">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3">
          <Link to="/" className="flex items-center gap-3">
            <span aria-hidden className="grid h-11 w-11 place-items-center rounded-xl bg-brand-600 text-xl text-white">जन</span>
            <span>
              <span className="block text-xl font-bold leading-tight text-brand-800">JanSahayak AI</span>
              <span className="block text-sm leading-tight text-leaf-700">{t('tagline')}</span>
            </span>
          </Link>
          <LanguageSelector />
        </div>
        <nav aria-label="Main" className="border-t border-brand-50">
          <ul className="mx-auto flex max-w-6xl gap-1 overflow-x-auto px-2 py-1.5">
            {NAV.map(([to, key, icon]) => (
              <li key={to} className="shrink-0">
                <NavLink
                  to={to}
                  end={to === '/'}
                  className={({ isActive }) =>
                    `flex min-h-[44px] items-center gap-2 rounded-lg px-3 text-base font-medium transition ${
                      isActive ? 'bg-brand-600 text-white' : 'text-slate-700 hover:bg-brand-50'
                    }`
                  }
                >
                  <span aria-hidden>{icon}</span>
                  {t(key)}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
        <p className="bg-leaf-50 px-4 py-1.5 text-center text-sm text-leaf-700">{t('banner')}</p>
      </header>

      <main id="main" className="mx-auto w-full max-w-6xl flex-1 px-4 py-6">
        <Outlet />
      </main>

      <footer className="border-t border-slate-200 bg-white px-4 py-4 text-center text-sm text-slate-500">
        JanSahayak AI · {t('tagline')}
      </footer>
    </div>
  );
}
