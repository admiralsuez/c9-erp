import React from 'react';

interface StatCardProps {
  label: string;
  value: string | number;
  icon?: React.ReactNode;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
  onClick?: () => void;
}

export const StatCard: React.FC<StatCardProps> = ({
  label,
  value,
  icon,
  trend,
  trendValue,
  onClick,
}) => {
  return (
    <div
      onClick={onClick}
      className={`card p-4 flex items-start justify-between ${
        onClick ? 'cursor-pointer hover:shadow-md transition-shadow' : ''
      }`}
    >
      <div>
        <p className="text-neutral-500 text-sm font-medium">{label}</p>
        <p className="text-2xl font-bold text-neutral-900 mt-2">{value}</p>
        {trendValue && (
          <p
            className={`text-xs mt-2 ${
              trend === 'up'
                ? 'text-success'
                : trend === 'down'
                  ? 'text-error'
                  : 'text-neutral-500'
            }`}
          >
            {trendValue}
          </p>
        )}
      </div>
      {icon && <div className="text-neutral-300 text-3xl">{icon}</div>}
    </div>
  );
};

export default StatCard;
