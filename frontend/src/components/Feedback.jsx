import { useApp } from '../context/AppContext';

export function Spinner({ label }) {
  const { t } = useApp();
  return (
    <div role="status" aria-live="polite" className="flex items-center gap-3 py-4 text-slate-600">
      <span className="h-6 w-6 animate-spin rounded-full border-4 border-brand-200 border-t-brand-600" aria-hidden />
      <span>{label || t('common.loading')}</span>
    </div>
  );
}

export function ErrorBanner({ message, onRetry }) {
  const { t } = useApp();
  if (!message) return null;
  return (
    <div role="alert" className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-red-800">
      <span>{message}</span>
      {onRetry && <button type="button" onClick={onRetry} className="btn-secondary !min-h-[40px]">{t('common.retry')}</button>}
    </div>
  );
}

export function Notice({ children }) {
  if (!children) return null;
  return <div className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">{children}</div>;
}

export function PageTitle({ title, subtitle }) {
  return (
    <div className="mb-5">
      <h1 className="text-2xl font-bold text-brand-800 sm:text-3xl">{title}</h1>
      {subtitle && <p className="mt-1 text-slate-600">{subtitle}</p>}
    </div>
  );
}
