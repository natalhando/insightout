import styles from './Chat.module.scss';
import { EmptyState } from '../EmptyState';
import { Message } from '../Message';
import { Loader } from '../Loader';

const Chat = ({ messages, isLoading, children }) => {
  return (
    <div className={styles.container}>
      {children ? children : (
        <>
          {messages && messages.length === 0 && <EmptyState />}
          {messages && messages.map((msg, index) => (
            <Message key={index} message={msg} />
          ))}
          {isLoading && <Loader />}
        </>
      )}
    </div>
  );
};

export { Chat };
