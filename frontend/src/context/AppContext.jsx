import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { translate } from '../lib/i18n';
import { api } from '../lib/api';

const Ctx = createContext(null);

export function AppProvider({ children }) {
  const [lang, setLangState] = useState(() => {
    try { return localStorage.getItem('jansahayak_lang') || 'en'; } catch { return 'en'; }
  });
  const [meta, setMeta] = useState(null);

  const setLang = useCallback((code) => {
    setLangState(code);
    try { localStorage.setItem('jansahayak_lang', code); } catch { /* storage unavailable */ }
  }, []);

  useEffect(() => { document.documentElement.lang = lang; }, [lang]);
  useEffect(() => { api.meta().then(setMeta).catch(() => setMeta(null)); }, []);

  const value = useMemo(() => ({ lang, setLang, meta, t: (key) => translate(lang, key) }), [lang, setLang, meta]);
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export const useApp = () => useContext(Ctx);
