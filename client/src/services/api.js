const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';
export const ACTIVITY_LABELS = {
  thinking: 'Thinking through your question',
  reviewing: 'Reviewing the data',
  schema: 'Checking the data schema',
  query: 'Querying the orders data',
  tool: 'Running a data tool',
  answer: 'Preparing your answer',
};
export const DEFAULT_ACTIVITY = ACTIVITY_LABELS.thinking;

export async function postChat(messages, onActivity) {
  const response = await fetch(`${API_URL}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages }),
  });

  if (!response.ok) {
    const data = await response.json();
    throw new Error(data.detail || 'Failed request');
  }

  const reader = response.body?.getReader();
  if (!reader) throw new Error('The server did not return a response stream');

  const decoder = new TextDecoder();
  let buffer = '';

  const handleEvent = (eventText) => {
    const dataLine = eventText.split('\n').find((line) => line.startsWith('data: '));
    if (!dataLine) return null;

    const event = JSON.parse(dataLine.slice(6));
    if (event.type === 'status') {
      onActivity?.(ACTIVITY_LABELS[event.code] ?? DEFAULT_ACTIVITY);
      return null;
    }
    if (event.type === 'error') throw new Error(event.message || 'Failed request');
    return event.type === 'result' ? event : null;
  };

  while (true) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
    const events = buffer.split('\n\n');
    buffer = events.pop() || '';

    for (const eventText of events) {
      const result = handleEvent(eventText);
      if (result) return result;
    }
    if (done) break;
  }

  throw new Error('The server ended the response before completing the request');
}
