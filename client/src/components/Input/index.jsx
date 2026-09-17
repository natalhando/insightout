import styles from './Input.module.scss';

const Input = ({
  input,
  setInput,
  handleSubmit,
  isLoading,
  placeholder = 'Ask about the orders table...'
}) => {
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className={styles.input}>
      <div className={styles.container}>
        <form onSubmit={handleSubmit} className={styles.form}>
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={isLoading}
            className={styles.textarea}
            rows={3}
          />
          <div className={styles.footer}>
            <span className={styles.helperText}>
              Enter to send · Shift+Enter for a new line
            </span>
            <button
              type="submit"
              disabled={isLoading || !input?.trim()}
              className={styles.button}
            >
              {isLoading ? 'Sending...' : 'Ask'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export { Input };
