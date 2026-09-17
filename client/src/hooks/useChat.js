import { useState } from 'react';

export function useChat() {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const sendMessage = async (userText) => {
    if (!userText.trim()) return;

    const newMessages = [...messages, { role: 'user', content: userText }];
    setMessages(newMessages);
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: newMessages }),
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Failed request');

      setMessages([...newMessages, { role: 'assistant', content: data.content }]);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return { messages, sendMessage, isLoading, error };
}