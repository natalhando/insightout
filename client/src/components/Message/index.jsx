import styles from './Message.module.scss';

const Message = ({ msg, message, role, content }) => {
  const item = msg || message || { role, content };
  const isUser = item?.role === 'user';
  const text = item?.content || '';

  // Split multi-paragraph text
  const paragraphs = text.split(/\n\n+/).filter(Boolean);

  return (
    <div className={`${styles.message} ${isUser ? styles.user : styles.assistant}`}>
      {isUser ? (
        <div>{text}</div>
      ) : (
        paragraphs.map((p, idx) => (
          <p key={idx} className={styles.paragraph}>
            {p}
          </p>
        ))
      )}
    </div>
  );
};

export { Message };
