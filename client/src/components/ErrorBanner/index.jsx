import styles from './ErrorBanner.module.scss';

const ErrorBanner = ({ error, message, children }) => {
    const content = error || message || children;
    if (!content) return null;

    return (
        <div className={styles.banner}>
            <strong>Error:</strong> {content}
        </div>
    );
};

export { ErrorBanner };
