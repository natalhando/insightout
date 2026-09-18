import { vi } from 'vitest';

export const messageFixture = [
  { role: 'user', content: 'Hello' },
  { role: 'assistant', content: 'Hi there' },
];

export const statusThinkingFixture = 'data: {"type":"status","code":"thinking"}\n\n';
export const resultHelloFixture = 'data: {"type":"result","message":"Hello world"}\n\n';

export function createStreamReader(events) {
  const read = vi.fn();

  for (const event of events) {
    read.mockResolvedValueOnce({
      value: new TextEncoder().encode(event),
      done: false,
    });
  }

  read.mockResolvedValueOnce({ value: undefined, done: true });

  return { read };
}

export function createFetchResponse({ ok = true, detail = '', streamEvents = [] } = {}) {
  const response = {
    ok,
    body: streamEvents.length
      ? {
          getReader: () => createStreamReader(streamEvents),
        }
      : null,
  };

  if (!ok) {
    response.json = vi.fn().mockResolvedValue({ detail });
  }

  return response;
}
