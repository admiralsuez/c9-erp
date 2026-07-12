import React from 'react';
import { ChevronRight } from 'lucide-react';

interface EntityListCardProps {
  title: string;
  subtitle?: string;
  description?: string;
  avatar?: React.ReactNode;
  badge?: React.ReactNode;
  onClick?: () => void;
  trailing?: React.ReactNode;
}

export const EntityListCard: React.FC<EntityListCardProps> = ({
  title,
  subtitle,
  description,
  avatar,
  badge,
  onClick,
  trailing,
}) => {
  return (
    <div
      onClick={onClick}
      className={`card p-4 flex items-center gap-4 ${
        onClick ? 'cursor-pointer hover:shadow-md transition-all' : ''
      }`}
    >
      {avatar && (
        <div className="w-12 h-12 rounded-full bg-primary-100 flex items-center justify-center flex-shrink-0">
          {avatar}
        </div>
      )}

      <div className="flex-grow min-w-0">
        <div className="flex items-center gap-2">
          <h3 className="font-semibold text-neutral-900 truncate">{title}</h3>
          {badge && <div>{badge}</div>}
        </div>
        {subtitle && <p className="text-sm text-neutral-500 truncate">{subtitle}</p>}
        {description && <p className="text-xs text-neutral-400 truncate mt-1">{description}</p>}
      </div>

      {trailing ? (
        <div className="flex-shrink-0">{trailing}</div>
      ) : onClick ? (
        <ChevronRight className="w-5 h-5 text-neutral-300 flex-shrink-0" />
      ) : null}
    </div>
  );
};

export default EntityListCard;
