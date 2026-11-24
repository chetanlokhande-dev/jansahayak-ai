import { useApp } from '../context/AppContext';
import { useSpeechInput, useSpeechOutput } from '../lib/voice';

export function MicButton({ onText }) {
  const { lang, t } = useApp();
  const { listening, error, start, stop, supported } = useSpeechInput(lang, onText);
  return (
    <div className="flex flex-col items-start">
      <button
        type="button"
        onClick={listening ? stop : start}
        aria-pressed={listening}
        aria-label={t('common.mic')}
        title={supported ? t('common.mic') : t('common.micUnsupported')}
        disabled={!supported}
        className={`btn !min-w-[48px] !px-3 ${listening ? 'animate-pulse bg-red-600 text-white' : 'btn-secondary'}`}
      >
        <span aria-hidden>🎤</span>
        <span className="sr-only sm:not-sr-only">{listening ? t('common.listening') : t('common.mic')}</span>
      </button>
      {(!supported || error === 'not-allowed') && (
        <span className="mt-1 text-xs text-red-700">{t('common.micUnsupported')}</span>
      )}
    </div>
  );
}

export function ListenButton({ text }) {
  const { lang, t } = useApp();
  const { speaking, speak, stop, supported } = useSpeechOutput(lang);
  if (!supported) return null;
  return (
    <button
      type="button"
      onClick={() => (speaking ? stop() : speak(text))}
      className="btn-secondary !min-h-[40px] !px-3 text-sm"
      aria-pressed={speaking}
    >
      <span aria-hidden>{speaking ? '⏹' : '🔊'}</span>
      {speaking ? t('common.stop') : t('common.listen')}
    </button>
  );
}
