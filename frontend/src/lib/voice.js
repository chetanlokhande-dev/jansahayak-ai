import { useCallback, useEffect, useRef, useState } from 'react';
import { LANGS } from './i18n';

const speechCode = (lang) => (LANGS.find((l) => l.code === lang) || LANGS[0]).speech;

/** Remove markdown symbols so text is read aloud naturally. */
export function plainText(text) {
  return String(text || '')
    .replace(/\*\*(.+?)\*\*/g, '$1')
    .replace(/_(.+?)_/g, '$1')
    .replace(/^#+\s*/gm, '')
    .replace(/^\s*[-*]\s+/gm, '')
    .replace(/\[S\d+\]/g, '')
    .replace(/\s+/g, ' ')
    .trim();
}

export const ttsSupported = () => typeof window !== 'undefined' && 'speechSynthesis' in window;
export const micSupported = () =>
  typeof window !== 'undefined' && !!(window.SpeechRecognition || window.webkitSpeechRecognition);

/** Speech-to-text using the browser's Web Speech API. */
export function useSpeechInput(lang, onText) {
  const [listening, setListening] = useState(false);
  const [error, setError] = useState('');
  const recRef = useRef(null);

  const stop = useCallback(() => {
    try { recRef.current && recRef.current.stop(); } catch { /* already stopped */ }
    setListening(false);
  }, []);

  const start = useCallback(() => {
    const Rec = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Rec) { setError('unsupported'); return; }
    setError('');
    const rec = new Rec();
    rec.lang = speechCode(lang);
    rec.interimResults = false;
    rec.maxAlternatives = 1;
    rec.onresult = (e) => {
      const text = Array.from(e.results).map((r) => r[0].transcript).join(' ');
      if (text) onText(text);
    };
    rec.onerror = (e) => { setError(e.error || 'error'); setListening(false); };
    rec.onend = () => setListening(false);
    recRef.current = rec;
    try { rec.start(); setListening(true); } catch { setListening(false); }
  }, [lang, onText]);

  useEffect(() => () => { try { recRef.current && recRef.current.abort(); } catch { /* noop */ } }, []);
  return { listening, error, start, stop, supported: micSupported() };
}

/** Text-to-speech using the browser's Speech Synthesis API. */
export function useSpeechOutput(lang) {
  const [speaking, setSpeaking] = useState(false);

  const stop = useCallback(() => {
    if (ttsSupported()) window.speechSynthesis.cancel();
    setSpeaking(false);
  }, []);

  const speak = useCallback((text) => {
    if (!ttsSupported()) return;
    window.speechSynthesis.cancel();
    const utter = new SpeechSynthesisUtterance(plainText(text));
    utter.lang = speechCode(lang);
    const voice = window.speechSynthesis.getVoices().find((v) => v.lang === utter.lang)
      || window.speechSynthesis.getVoices().find((v) => v.lang.startsWith(lang));
    if (voice) utter.voice = voice;
    utter.rate = 0.95;
    utter.onend = () => setSpeaking(false);
    utter.onerror = () => setSpeaking(false);
    setSpeaking(true);
    window.speechSynthesis.speak(utter);
  }, [lang]);

  useEffect(() => stop, [stop]);
  return { speaking, speak, stop, supported: ttsSupported() };
}
