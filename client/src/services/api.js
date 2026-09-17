const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

export async function postChat(messages) {
  const response = await fetch(`${API_URL}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages }),
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || 'Failed request');
  }

  return data;
}
