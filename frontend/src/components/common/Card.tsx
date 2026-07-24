import React, { ReactNode } from 'react';
import clsx from 'clsx';

interface CardProps {
  title?: string;
  subtitle?: string;
  children: ReactNode;
  className?: string;
  action?: ReactNode;
}

function Card({ title, subtitle, children, className, action }: CardProps) {
  return (
    <section className={clsx('glass-card p-5 md:p-6', className)}>
      {(title || subtitle || action) && (
        <div className="panel-header">
          <div>
            {title && <h3 className="text-lg font-semibold text-slate-100">{title}</h3>}
            {subtitle && <p className="mt-1 text-sm text-slate-400">{subtitle}</p>}
          </div>
          {action}
        </div>
      )}
      <div className="relative z-[1]">{children}</div>
    </section>
  );
}

export default Card;
