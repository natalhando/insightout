import styles from './Loader.module.scss';

const Loader = ({ text = 'Thinking...' }) => {
    return (
        <div className={styles.loader}>{text}</div>
    );
};

export { Loader };
