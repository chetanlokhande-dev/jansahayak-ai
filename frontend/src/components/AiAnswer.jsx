import { useApp } from '../context/AppContext';
import RichText from './RichText';
import SourceList from './SourceList';
import { ListenButton } from './VoiceControls';
import { Notice } from './Feedback';

function Group({ title, items, tone }) {
  if (!items || !items.length) return null;
  const tones = {
    green: 'border-leaf-200 bg-leaf-50 text-leaf-700',
    blue: 'border-brand-200 bg-brand-50 text-brand-800',
    amber: 'border-amber-200 bg-amber-50 text-amber-900',
  };
  return (
    <details className={`mt-2 rounded-xl border p-3 ${tones[tone]}`}>
      <summary className="cursor-pointer font-semibold">{title} ({items.length})</summary>
      <ul className="mt-2 list-disc space-y-1 pl-5 text-sm">{items.map((i, n) => <li key={n}>{i}</li>)}</ul>
    </details>
  );
}

export default function AiAnswer({ message, onFollowUp }) {
  const { t } = useApp();
  return (
    <div className="space-y-2">
      <RichText text={message.content} />
      <Notice>{message.notice}</Notice>
      <Group title={t('ai.verified')} items={message.verified} tone="green" />
      <Group title={t('ai.inferred')} items={message.inferred} tone="blue" />
      <Group title={t('ai.unavailable')} items={message.unavailable} tone="amber" />
      <SourceList sources={message.sources} />
      {message.follow_ups && message.follow_ups.length > 0 && (
        <div className="pt-2">
          <p className="mb-1 text-sm font-semibold text-slate-500">{t('chat.followups')}</p>
          <div className="flex flex-wrap gap-2">
            {message.follow_ups.map((q, i) => (
              <button key={i} type="button" onClick={() => onFollowUp(q)} className="chip border border-brand-200 bg-white text-brand-700 hover:bg-brand-50">
                {q}
              </button>
            ))}
          </div>
        </div>
      )}
      <div className="pt-1"><ListenButton text={message.content} /></div>
    </div>
  );
}
