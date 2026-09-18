import { useState } from 'react';

import { DEFAULT_ACTIVITY, postChat } from '../services/api';

export function useChat() {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [activity, setActivity] = useState(DEFAULT_ACTIVITY);
  const [error, setError] = useState(null);

  const sendMessage = async (userText) => {
    if (!userText.trim()) return;

    const newMessages = [...messages, { role: 'user', content: userText }];
    setMessages(newMessages);
    setIsLoading(true);
    setActivity(DEFAULT_ACTIVITY);
    setError(null);

    try {
      const data = await postChat(newMessages, setActivity);
      setMessages([...newMessages, {
        role: 'assistant',
        content: data.message,
        suggestions: Array.isArray(data.suggestions) ? data.suggestions : []
      }]);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return { messages, sendMessage, isLoading, activity, error };
}