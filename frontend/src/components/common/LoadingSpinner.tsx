import React from 'react';

interface LoadingSpinnerProps {
  label?: string;
}

function LoadingSpinner({ label = 'Loading EQIP intelligence…' }: LoadingSpinnerProps) {
  return (
    <div className="flex min-h-[200px] flex-col items-center justify-center gap-4 text-slate-300">
      <div className="h-12 w-12 animate-spin rounded-full border-2 border-cyan-400/20 border-t-cyan-300" />
      <p className="text-sm text-slate-400">{label}</p>
    </div>
  );
}

export default LoadingSpinner;
