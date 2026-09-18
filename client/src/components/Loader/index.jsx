import styles from './Loader.module.scss';

const Loader = ({ text = 'Thinking...' }) => {
    return (
        <div className={styles.loader} role="status" aria-live="polite">
            <span className={styles.dots} aria-hidden="true">
                <span />
                <span />
                <span />
            </span>
            <span>{text}</span>
        </div>
    );
};

export { Loader };
