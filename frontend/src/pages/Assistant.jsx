import { useCallback, useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { api } from '../lib/api';
import AiAnswer from '../components/AiAnswer';
import { MicButton } from '../components/VoiceControls';
import { ErrorBanner, PageTitle, Spinner } from '../components/Feedback';

export default function Assistant() {
  const { lang, t } = useApp();
  const [params, setParams] = useSearchParams();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [convId, setConvId] = useState(params.get('c'));
  const [docId, setDocId] = useState(params.get('doc'));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const bottomRef = useRef(null);
  const autoSent = useRef(false);
  const lastText = useRef('');

  const send = useCallback(async (text) => {
    const message = text.trim();
    if (!message || loading) return;
    lastText.current = message;
    setError('');
    setInput('');
    setMessages((m) => [...m, { role: 'user', content: message }]);
    setLoading(true);
    try {
      const res = await api.chat(message, lang, convId, docId);
      setConvId(res.conversation_id);
      setMessages((m) => [...m, { role: 'assistant', ...res, content: res.answer }]);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [lang, convId, docId, loading]);

  // Load an earlier conversation from History (?c=ID).
  useEffect(() => {
    const id = params.get('c');
    if (!id) return;
    api.conversation(id)
      .then((res) => { setMessages(res.messages); setConvId(id); if (res.conversation.document_id) setDocId(res.conversation.document_id); })
      .catch((e) => setError(e.message));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Auto-send a question passed from the Home page (?q=...).
  useEffect(() => {
    const q = params.get('q');
    if (q && !autoSent.current) {
      autoSent.current = true;
      send(q);
      const next = new URLSearchParams(params);
      next.delete('q');
      setParams(next, { replace: true });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => { bottomRef.current && bottomRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' }); }, [messages, loading]);

  const newChat = () => { setMessages([]); setConvId(null); setDocId(null); setError(''); setParams({}, { replace: true }); };

  return (
    <div className="mx-auto flex max-w-3xl flex-col">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <PageTitle title={t('nav.assistant')} subtitle={t('chat.empty')} />
        {messages.length > 0 && <button type="button" onClick={newChat} className="btn-secondary !min-h-[40px]">{t('chat.new')}</button>}
      </div>

      {docId && <div className="mb-3 rounded-xl border border-leaf-200 bg-leaf-50 p-3 text-leaf-700">📄 {t('chat.doc')}</div>}

      <div className="space-y-4 pb-4" aria-live="polite">
        {messages.map((m, i) =>
          m.role === 'user' ? (
            <div key={i} className="flex justify-end">
              <div className="max-w-[85%] rounded-2xl rounded-br-md bg-brand-600 px-4 py-3 text-white">{m.content}</div>
            </div>
          ) : (
            <div key={i} className="card max-w-[95%] rounded-bl-md p-4">
              <AiAnswer message={m} onFollowUp={send} />
            </div>
          ),
        )}
        {loading && <div className="card p-4"><Spinner label={t('chat.thinking')} /></div>}
        <ErrorBanner message={error} onRetry={lastText.current ? () => send(lastText.current) : undefined} />
        <div ref={bottomRef} />
      </div>

      <form
        onSubmit={(e) => { e.preventDefault(); send(input); }}
        className="sticky bottom-0 -mx-4 flex items-end gap-2 border-t border-slate-200 bg-slate-50/95 p-4 backdrop-blur"
      >
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(input); } }}
          placeholder={t('chat.placeholder')}
          aria-label={t('chat.placeholder')}
          rows={1}
          maxLength={2000}
          className="input max-h-40 flex-1 resize-none"
        />
        <MicButton onText={(text) => setInput((v) => (v ? `${v} ${text}` : text))} />
        <button type="submit" disabled={loading || !input.trim()} className="btn-primary">{t('chat.send')}</button>
      </form>
    </div>
  );
}
