import styles from './EmptyState.module.scss';

const EmptyState = ({ suggestions = [], onSelect }) => {
  if (!suggestions || suggestions.length === 0) return null;

  return (
    <div className={styles.wrapper}>
      <hr className={styles.divider} />
      <div className={styles.container}>
        <span className={styles.title}>What would you like to know?</span>
        {suggestions.map((item, index) => (
          <button
            key={index}
            type="button"
            className={styles.button}
            onClick={() => onSelect && onSelect(item)}
          >
            {item}
          </button>
        ))}
      </div>
    </div>
  );
};

export { EmptyState };

