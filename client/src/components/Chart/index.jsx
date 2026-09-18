import Highcharts from 'highcharts';
import HighchartsReactModule from 'highcharts-react-official';

import styles from '../Message/Message.module.scss';

const HighchartsReact = HighchartsReactModule.default || HighchartsReactModule;

export default function Chart({ chart }) {
  const options = {
    chart: {
      type: 'column',
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
      pointFormat: '<b>{point.y}</b>'
    },
    xAxis: {
      categories: chart.data.map((item) => item.label),
      title: { text: null },
      labels: {
        autoRotation: [-45, -90],
        style: { fontSize: '12px' }
      }
    },
    yAxis: {
      title: { text: null },
      labels: { style: { fontSize: '12px' } }
    },
    legend: { enabled: false },
    plotOptions: {
      column: {
        color: '#111827',
        borderRadius: 5,
        pointPadding: 0.12,
        groupPadding: 0.08
      }
    },
    series: [{
      name: 'Value',
      data: chart.data.map((item) => item.value)
    }]
  };

  return (
    <div className={styles.chart} role="img" aria-label={chart.title}>
      <HighchartsReact highcharts={Highcharts} options={options} />
    </div>
  );
}
