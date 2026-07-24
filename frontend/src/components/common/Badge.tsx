import React, { ReactNode } from 'react';
import clsx from 'clsx';
import { HealthTone } from '../../types';

interface BadgeProps {
  children: ReactNode;
  tone?: HealthTone;
  className?: string;
}

const toneClasses: Record<HealthTone, string> = {
  success: 'bg-emerald-500/15 text-emerald-300 ring-emerald-400/20',
  warning: 'bg-amber-500/15 text-amber-300 ring-amber-400/20',
  danger: 'bg-rose-500/15 text-rose-300 ring-rose-400/20',
  info: 'bg-cyan-500/15 text-cyan-300 ring-cyan-400/20',
};

function Badge({ children, tone = 'info', className }: BadgeProps) {
  return (
    <span
      className={clsx(
        'inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold ring-1 ring-inset',
        toneClasses[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}

export default Badge;
