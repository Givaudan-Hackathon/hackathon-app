import { useId, useRef, type FormEvent, type KeyboardEvent } from 'react';
import {
  ArrowUp,
  Check,
  LoaderCircle,
  MessageCircle,
  Sparkles,
} from 'lucide-react';
import type { ConversationState } from './model.ts';

export function ConversationPanel({
  state,
  onSend,
  draft,
  onDraftChange,
  compact = false,
}: {
  state: ConversationState;
  onSend: (message: string) => Promise<boolean>;
  draft: string;
  onDraftChange: (value: string) => void;
  compact?: boolean;
}) {
  const id = useId();
  const ref = useRef<HTMLTextAreaElement>(null);
  async function submit(event?: FormEvent) {
    event?.preventDefault();
    const text = draft.trim();
    if (!text || state.pending) return;
    if (await onSend(text)) onDraftChange('');
  }
  function keyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (
      event.key === 'Enter' &&
      !event.shiftKey &&
      !event.nativeEvent.isComposing &&
      window.matchMedia('(pointer: fine)').matches
    ) {
      event.preventDefault();
      void submit();
    }
  }
  return (
    <section
      className="conversation-panel"
      aria-label="Conversation avec l’assistant"
    >
      <div className="conversation-label">
        <span className="assistant-mark">
          <Sparkles size={18} aria-hidden="true" />
        </span>
        <div>
          <strong>Votre assistant arômes</strong>
          <span>
            <span className="online-dot" /> À l’écoute de votre projet
          </span>
        </div>
        <span className="conversation-demo">Échanges simulés</span>
      </div>
      {state.messages.length > 2 ? (
        <details className="conversation-history">
          <summary>
            <MessageCircle size={15} aria-hidden="true" /> Voir les échanges
            précédents ({state.messages.length - 2})
          </summary>
          <div>
            {state.messages.slice(0, -2).map((message) => (
              <div
                className={`history-message history-${message.role}`}
                key={message.id}
              >
                <strong>
                  {message.role === 'user' ? 'Vous' : 'L’assistant'}
                </strong>
                <p>{message.text}</p>
              </div>
            ))}
          </div>
        </details>
      ) : null}
      <div
        className="recent-messages"
        role="log"
        aria-live="polite"
        aria-relevant="additions text"
        aria-busy={state.pending}
      >
        {state.messages.slice(-2).map((message) => (
          <div className={`chat-message chat-${message.role}`} key={message.id}>
            <span className="message-author">
              {message.role === 'user' ? (
                'Vous'
              ) : (
                <>
                  <Sparkles size={13} aria-hidden="true" /> Notre assistant
                </>
              )}
            </span>
            <p>{message.text}</p>
          </div>
        ))}
        {state.pending ? (
          <div className="assistant-loading">
            <LoaderCircle size={17} className="spinner" aria-hidden="true" />{' '}
            L’assistant prépare votre réponse…
          </div>
        ) : null}
      </div>
      {state.sessionReset ? (
        <p className="notice" role="status">
          La session a redémarré. Reprécisez votre projet pour retrouver des
          propositions.
        </p>
      ) : null}
      {state.error ? (
        <div className="error-notice" role="alert">
          {state.error}
        </div>
      ) : null}
      <details
        className="chat-composer-disclosure"
        open={!compact || Boolean(state.error)}
      >
        <summary>
          Une précision ou une question ? <span aria-hidden="true">+</span>
        </summary>
        <form
          onSubmit={(event) => void submit(event)}
          className="chat-composer"
        >
          <label htmlFor={id}>
            {state.snapshot?.etape === 'relance'
              ? 'Précisons votre idée'
              : 'Une précision ou une question ?'}
          </label>
          <div className="chat-input-wrap">
            <textarea
              ref={ref}
              id={id}
              name="message"
              value={draft}
              onChange={(event) => onDraftChange(event.target.value)}
              onKeyDown={keyDown}
              rows={2}
              maxLength={500}
              required
              placeholder="Par exemple : je souhaite une version bio…"
              disabled={state.pending}
            />
            <button
              type="submit"
              className="send-button"
              disabled={state.pending}
              aria-label="Envoyer ma précision"
            >
              <ArrowUp size={20} aria-hidden="true" />
            </button>
          </div>
          <div className="composer-bottom">
            <span>
              <Check size={12} aria-hidden="true" /> Vous pouvez ajuster votre
              idée à tout moment
            </span>
            <span>{draft.length}/500</span>
          </div>
        </form>
      </details>
    </section>
  );
}
