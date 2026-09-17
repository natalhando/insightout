import styles from './KeepGoing.module.scss';

const KeepGoing = ({ suggestions = [], onSelect }) => {
  if (!suggestions || suggestions.length === 0) return null;

  return (
    <div className={styles.wrapper}>
      <hr className={styles.divider} />
      <div className={styles.container}>
        <span className={styles.label}>KEEP GOING</span>
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

export { KeepGoing };

