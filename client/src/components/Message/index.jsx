import styles from './Message.module.scss';
import { Children, isValidElement, lazy, Suspense } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
const Chart = lazy(() => import('../Chart'));

const isChart = (className, value) => {
  if (!className?.includes('language-chart')) return false;

  try {
    const chart = JSON.parse(value);
    return chart.type === 'bar'
      && typeof chart.title === 'string'
      && chart.title.trim().length > 0
      && Array.isArray(chart.data)
      && chart.data.length > 0
      && chart.data.every((item) => (
        typeof item === 'object'
        && item !== null
        && typeof item.label === 'string'
        && Number.isFinite(item.value)
      ));
  } catch {
    return false;
  }
};

const Message = ({ msg, message, role, content }) => {
  const item = msg || message || { role, content };
  const isUser = item?.role === 'user';
  const text = item?.content || '';

  return (
    <div className={`${styles.message} ${isUser ? styles.user : styles.assistant}`}>
      {isUser ? (
        <div>{text}</div>
      ) : (
        <div className={styles.markdown}>
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              pre({ children, ...props }) {
                const containsChart = Children.toArray(children).some(
                  (child) => isValidElement(child) && child.type === Chart
                );

                return containsChart
                  ? children
                  : <pre {...props}>{children}</pre>;
              },
              code({ className, children, ...props }) {
                const value = String(children).replace(/\n$/, '');

                if (isChart(className, value)) {
                  return (
                    <Suspense fallback={null}>
                      <Chart chart={JSON.parse(value)} />
                    </Suspense>
                  );
                }

                return <code className={className} {...props}>{children}</code>;
              }
            }}
          >
            {text}
          </ReactMarkdown>
        </div>
      )}
    </div>
  );
};

export { Message };
