import styles from './Header.module.scss';

const Header = ({ title = 'InsightOut' }) => {
  return (
    <header className={styles.header}>
      <div className={styles.container}>
        <h1 className={styles.title}>{title}</h1>
      </div>
    </header>
  );
};

export { Header };