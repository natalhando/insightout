import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
  createFetchResponse,
  messageFixture,
  resultHelloFixture,
  statusThinkingFixture,
} from './fixtures.js';

async function loadApiModule() {
  return import('../api.js');
}

describe('postChat', () => {
  beforeEach(() => {
    vi.resetModules();
    vi.stubEnv('VITE_API_URL', 'http://localhost:4321');
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllEnvs();
    vi.resetModules();
  });

  it('should post transformed messages and resolve the first result event while emitting status updates', async () => {
    const { ACTIVITY_LABELS, postChat } = await loadApiModule();
    const fetchMock = vi.fn().mockResolvedValue(
      createFetchResponse({
        streamEvents: [statusThinkingFixture, resultHelloFixture],
      }),
    );
    vi.stubGlobal('fetch', fetchMock);

    const onActivity = vi.fn();
    const result = await postChat(messageFixture, onActivity);

    expect(fetchMock).toHaveBeenCalledWith(
      'http://localhost:4321/api/chat',
      expect.objectContaining({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: [
            { role: 'user', content: 'Hello' },
            { role: 'model', content: 'Hi there' },
          ],
        }),
      }),
    );
    expect(onActivity).toHaveBeenCalledWith(ACTIVITY_LABELS.thinking);
    expect(result).toEqual({ type: 'result', answer: 'Hello world' });
  });

  it('should throw the backend detail when the HTTP response is unsuccessful', async () => {
    const { postChat } = await loadApiModule();
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        createFetchResponse({
          ok: false,
          detail: 'Nope',
        }),
      ),
    );

    await expect(postChat([{ role: 'user', content: 'Hello' }])).rejects.toThrow('Nope');
  });

  it('should use the default activity label when the server status code is unknown', async () => {
    const { DEFAULT_ACTIVITY, postChat } = await loadApiModule();
    const unknownStatus = 'data: {"type":"status","code":"unknown"}\n\n';
    const followupResult = 'data: {"type":"result","answer":"still good"}\n\n';

    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        createFetchResponse({
          streamEvents: [unknownStatus, followupResult],
        }),
      ),
    );

    const onActivity = vi.fn();
    const result = await postChat([{ role: 'user', content: 'Test' }], onActivity);

    expect(onActivity).toHaveBeenCalledWith(DEFAULT_ACTIVITY);
    expect(result).toEqual({ type: 'result', answer: 'still good' });
  });

  it('should throw a server error when the stream ends without a result', async () => {
    const { postChat } = await loadApiModule();
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        createFetchResponse({
          streamEvents: [statusThinkingFixture],
        }),
      ),
    );

    await expect(postChat([{ role: 'user', content: 'Hello' }])).rejects.toThrow(
      'The server ended the response before completing the request',
    );
  });

  it('should throw the backend error message when the event stream reports an error', async () => {
    const { postChat } = await loadApiModule();
    const errorEvent = 'data: {"type":"error","message":"Failure"}\n\n';

    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        createFetchResponse({
          streamEvents: [errorEvent],
        }),
      ),
    );

    await expect(postChat([{ role: 'user', content: 'Hello' }])).rejects.toThrow('Failure');
  });
});
