import { useCallback, useEffect, useReducer, useRef } from 'react';
import type { ConversationService } from '../../services/conversation-service.ts';
import { conversationReducer, initialConversation } from './model.ts';

export function useConversation(service: ConversationService) {
  const [state, dispatch] = useReducer(
    conversationReducer,
    initialConversation,
  );
  const pendingRef = useRef(false);
  const controller = useRef<AbortController | null>(null);
  const generation = useRef(0);
  const lastInput = useRef<{
    message: string;
    pisteId?: string;
    displayText?: string;
  } | null>(null);
  useEffect(() => () => controller.current?.abort(), []);
  const send = useCallback(
    async (message: string, pisteId?: string, displayText?: string) => {
      if (pendingRef.current) return null;
      lastInput.current = { message, pisteId, displayText };
      pendingRef.current = true;
      const currentGeneration = ++generation.current;
      controller.current = new AbortController();
      const previousSession = state.snapshot?.session_id ?? null;
      dispatch({
        type: 'start',
        message: {
          id: crypto.randomUUID(),
          role: 'user',
          text: displayText ?? message,
        },
      });
      try {
        const snapshot = await service.send(
          { session_id: previousSession, message, piste_id: pisteId ?? null },
          { signal: controller.current.signal },
        );
        if (generation.current !== currentGeneration) return null;
        dispatch({
          type: 'success',
          snapshot,
          previousSession,
          message: {
            id: crypto.randomUUID(),
            role: 'assistant',
            text: snapshot.reponse,
          },
        });
        return snapshot;
      } catch (error) {
        if (
          generation.current === currentGeneration &&
          !(error instanceof DOMException && error.name === 'AbortError')
        )
          dispatch({
            type: 'failure',
            error:
              error instanceof Error
                ? error.message
                : 'Un problème est survenu. Réessayez.',
          });
        return null;
      } finally {
        if (generation.current === currentGeneration)
          pendingRef.current = false;
      }
    },
    [service, state.snapshot?.session_id],
  );
  const reset = useCallback(() => {
    generation.current++;
    controller.current?.abort();
    pendingRef.current = false;
    lastInput.current = null;
    dispatch({ type: 'reset' });
  }, []);
  const cancel = useCallback(() => {
    generation.current++;
    controller.current?.abort();
    pendingRef.current = false;
    dispatch({ type: 'cancel' });
  }, []);
  const retry = useCallback(() => {
    const input = lastInput.current;
    return input
      ? send(input.message, input.pisteId, input.displayText)
      : Promise.resolve(null);
  }, [send]);
  return { state, send, reset, cancel, retry };
}
