import React from 'react';

interface ChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    backgroundColor?: string;
    borderColor?: string;
  }[];
}

interface ReportChartProps {
  title: string;
  type: 'bar' | 'line' | 'pie';
  data: ChartData;
  height?: number;
}

/**
 * Report visualization chart component
 * Displays metrics in various chart formats
 */
const ReportChart: React.FC<ReportChartProps> = ({
  title,
  type,
  data,
  height = 400,
}) => {
  const colors = [
    '#3b82f6', // blue
    '#10b981', // green
    '#f59e0b', // amber
    '#ef4444', // red
    '#8b5cf6', // purple
    '#ec4899', // pink
    '#06b6d4', // cyan
    '#f97316', // orange
  ];

  // Ensure datasets have colors
  const coloredData: ChartData = {
    ...data,
    datasets: data.datasets.map((dataset, idx) => ({
      ...dataset,
      backgroundColor: dataset.backgroundColor || colors[idx % colors.length],
      borderColor: dataset.borderColor || colors[idx % colors.length],
    })),
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
      
      <div style={{ position: 'relative', height: `${height}px` }}>
        {type === 'bar' && (
          <div className="flex items-end justify-start gap-2 h-full">
            {coloredData.labels.map((label, idx) => (
              <div key={idx} className="flex-1 flex flex-col items-center">
                <div className="relative w-full flex justify-center" style={{ height: `${height - 40}px` }}>
                  <div
                    className="bg-blue-500 rounded-t opacity-80 hover:opacity-100 transition-opacity w-10"
                    style={{
                      height: `${
                        coloredData.datasets.length > 0
                          ? (coloredData.datasets[0].data[idx] / Math.max(...coloredData.datasets[0].data)) * (height - 40)
                          : 0
                      }px`,
                    }}
                    title={`${label}: ${coloredData.datasets[0]?.data[idx] || 0}`}
                  />
                </div>
                <span className="text-xs text-gray-600 mt-2 text-center">{label}</span>
              </div>
            ))}
          </div>
        )}

        {type === 'line' && (
          <svg width="100%" height="100%" style={{ display: 'block' }}>
            <polyline
              fill="none"
              stroke="#3b82f6"
              strokeWidth="2"
              points={coloredData.labels
                .map((_, idx) => {
                  const x = (idx / (coloredData.labels.length - 1 || 1)) * (100 - 10) + 5;
                  const value = coloredData.datasets[0]?.data[idx] || 0;
                  const maxValue = Math.max(...coloredData.datasets[0]?.data, 1);
                  const y = height - (value / maxValue) * (height - 40) - 20;
                  return `${(x / 100) * (100 * 0.9)},${y}`;
                })
                .join(' ')}
            />
          </svg>
        )}

        {type === 'pie' && (
          <div className="flex items-center justify-center h-full">
            <div className="flex gap-8">
              {coloredData.datasets[0]?.data.map((value, idx) => {
                const total = coloredData.datasets[0].data.reduce((a, b) => a + b, 0);
                const percentage = ((value / total) * 100).toFixed(1);
                return (
                  <div key={idx} className="flex flex-col items-center">
                    <div
                      className="w-16 h-16 rounded-full flex items-center justify-center text-white font-bold"
                      style={{ backgroundColor: colors[idx % colors.length] }}
                    >
                      {percentage}%
                    </div>
                    <span className="text-sm text-gray-700 mt-2">{coloredData.labels[idx]}</span>
                    <span className="text-xs text-gray-500">{value}</span>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ReportChart;
