import styles from './Message.module.scss';
import { Children, isValidElement } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import Highcharts from 'highcharts';
import HighchartsReactModule from 'highcharts-react-official';

const HighchartsReact = HighchartsReactModule.default || HighchartsReactModule;

const Chart = ({ chart }) => {
  const isPie = chart.type === 'pie';
  const options = {
    chart: {
      type: isPie ? 'pie' : 'bar',
      backgroundColor: 'transparent',
      height: 360,
      spacing: [12, 0, 12, 0]
    },
    title: {
      text: chart.title,
      align: 'left',
      style: { fontSize: '16px', fontWeight: '600' }
    },
    credits: { enabled: false },
    tooltip: {
      pointFormat: isPie ? '<b>{point.y}</b>' : '<b>{point.y}</b>'
    },
    xAxis: isPie ? undefined : {
      categories: chart.data.map((item) => item.label),
      title: { text: null },
      labels: { style: { fontSize: '12px' } }
    },
    yAxis: isPie ? undefined : {
      min: 0,
      title: { text: null },
      labels: { style: { fontSize: '12px' } }
    },
    legend: { enabled: isPie },
    plotOptions: {
      bar: {
        color: '#111827',
        borderRadius: 5,
        pointPadding: 0.12,
        groupPadding: 0.08
      },
      pie: {
        allowPointSelect: true,
        cursor: 'pointer',
        dataLabels: {
          enabled: true,
          format: '{point.name}: {point.percentage:.1f}%'
        }
      }
    },
    series: [{
      name: isPie ? chart.title : 'Value',
      data: isPie
        ? chart.data.map((item) => ({ name: item.label, y: Number(item.value) }))
        : chart.data.map((item) => Number(item.value))
    }]
  };

  return (
    <div className={styles.chart} role="img" aria-label={chart.title}>
      <HighchartsReact highcharts={Highcharts} options={options} />
    </div>
  );
};

const isChart = (className, value) => {
  if (!className?.includes('language-chart')) return false;

  try {
    const chart = JSON.parse(value);
    return (chart.type === 'bar' || chart.type === 'pie')
      && typeof chart.title === 'string'
      && Array.isArray(chart.data)
      && chart.data.length > 0
      && chart.data.every((item) => (
        typeof item.label === 'string' && Number.isFinite(Number(item.value))
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
                  return <Chart chart={JSON.parse(value)} />;
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
