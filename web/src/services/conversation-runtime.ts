import { createHttpConversationService } from './adapters/http-conversation.ts';
import { createMockConversationService } from './adapters/mock-conversation.ts';

export function createConversationRuntime(env = import.meta.env) {
  const mode = env.VITE_CONVERSATION_MODE ?? 'http';
  if (mode === 'demo')
    return { mode: 'demo' as const, service: createMockConversationService() };
  if (mode !== 'http')
    throw new Error('VITE_CONVERSATION_MODE doit valoir http ou demo.');
  return {
    mode: 'http' as const,
    service: createHttpConversationService({
      endpoint: env.VITE_CONVERSATION_ENDPOINT ?? '/api/conversation',
      timeoutMs: Number(env.VITE_CONVERSATION_TIMEOUT_MS ?? 35_000),
    }),
  };
}
