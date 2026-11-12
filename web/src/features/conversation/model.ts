import type { ConversationSnapshot } from '../../services/conversation-service.ts';

export type Message = { id: string; role: 'user' | 'assistant'; text: string };
export type ConversationState = {
  snapshot: ConversationSnapshot | null;
  messages: Message[];
  pending: boolean;
  error: string | null;
  sessionReset: boolean;
};
export const initialConversation: ConversationState = {
  snapshot: null,
  messages: [],
  pending: false,
  error: null,
  sessionReset: false,
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
        messages: sessionReset
          ? [action.message]
          : [...state.messages, action.message],
      };
    }
    case 'failure':
      return { ...state, pending: false, error: action.error };
    case 'reset':
      return { ...initialConversation, messages: [] };
  }
}
