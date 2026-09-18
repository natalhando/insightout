import { useState } from 'react';
import { useChat } from './hooks/useChat';
import { Header } from './components/Header';
import { Layout } from './components/Layout';
import { Message } from './components/Message';
import { KeepGoing } from './components/KeepGoing';
import { EmptyState } from './components/EmptyState';
import { Loader } from './components/Loader';
import { ErrorBanner } from './components/ErrorBanner';
import { Input } from './components/Input';

const DEFAULT_SUGGESTIONS = [
  'What was the average order value each month?',
  'Which products drove the most revenue growth?',
  'How did customer counts change over this period?'
];

export default function App() {
  const { messages, sendMessage, isLoading, activity, error } = useChat();
  const [input, setInput] = useState('');
  const latestAssistantMessage = [...messages].reverse().find((msg) => msg.role === 'assistant');
  const followUpSuggestions = latestAssistantMessage?.suggestions ?? [];

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    sendMessage(input);
    setInput('');
  };

  const handleSelectSuggestion = (suggestion) => {
    sendMessage(suggestion);
  };

  return (
    <>
      <Header />

      <Layout>
        {messages.length === 0 && (
          <EmptyState
            suggestions={DEFAULT_SUGGESTIONS}
            onSelect={handleSelectSuggestion}
          />
        )}

        {messages.map((msg, index) => (
          <Message key={`${msg.role}-${index}`} message={msg} />
        ))}

        {isLoading && <Loader text={activity} />}

        {messages.length > 0 && !isLoading && (
          <KeepGoing
            suggestions={followUpSuggestions}
            onSelect={handleSelectSuggestion}
          />
        )}

        {error && <ErrorBanner error={error} />}
      </Layout>

      <Input
        input={input}
        setInput={setInput}
        handleSubmit={handleSubmit}
        isLoading={isLoading}
        placeholder="Ask about the orders table..."
      />
    </>
  );
}