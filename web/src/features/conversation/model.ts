import type { ConversationSnapshot } from '../../services/conversation-service.ts';

export type Message = { id: string; role: 'user' | 'assistant'; text: string };
export type ConversationState = {
  snapshot: ConversationSnapshot | null;
  messages: Message[];
  pending: boolean;
  error: string | null;
  sessionReset: boolean;
  notice: string | null;
  pendingMessageId: string | null;
};
export const initialConversation: ConversationState = {
  snapshot: null,
  messages: [],
  pending: false,
  error: null,
  sessionReset: false,
  notice: null,
  pendingMessageId: null,
};
export type ConversationAction =
  | { type: 'start'; message: Message }
  | {
      type: 'success';
      snapshot: ConversationSnapshot;
      message: Message;
      previousSession: string | null;
    }
  | { type: 'failure'; error: string }
  | { type: 'cancel' }
  | { type: 'reset' };
export function conversationReducer(
  state: ConversationState,
  action: ConversationAction,
): ConversationState {
  switch (action.type) {
    case 'start':
      return {
        ...state,
        pending: true,
        error: null,
        notice: null,
        pendingMessageId: action.message.id,
        messages: [...state.messages, action.message],
      };
    case 'success': {
      const sessionReset = Boolean(
        action.previousSession &&
        action.previousSession !== action.snapshot.session_id,
      );
      return {
        ...state,
        snapshot: action.snapshot,
        pending: false,
        error: null,
        sessionReset,
        pendingMessageId: null,
        notice: null,
        messages: sessionReset
          ? [
              ...state.messages.filter(
                (message) => message.id === state.pendingMessageId,
              ),
              action.message,
            ]
          : [...state.messages, action.message],
      };
    }
    case 'failure':
      return {
        ...state,
        pending: false,
        error: action.error,
        pendingMessageId: null,
        messages: state.messages.filter(
          (message) => message.id !== state.pendingMessageId,
        ),
      };
    case 'cancel':
      return {
        ...state,
        pending: false,
        error: null,
        pendingMessageId: null,
        notice: 'L’attente a été annulée. Votre saisie est conservée.',
        messages: state.messages.filter(
          (message) => message.id !== state.pendingMessageId,
        ),
      };
    case 'reset':
      return { ...initialConversation, messages: [] };
  }
}
