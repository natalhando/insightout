import styles from './Layout.module.scss';

const Layout = ({ children }) => {
  return (
    <main className={styles.container}>
      {children}
    </main>
  );
};

export { Layout };
