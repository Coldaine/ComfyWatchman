interface StatCardProps {
  label: string;
  value: number | string;
  variant?: 'default' | 'success' | 'warning' | 'danger';
}

export function StatCard({ label, value, variant = 'default' }: StatCardProps) {
  const variantStyles = {
    default: 'border-border',
    success: 'border-green-500/30 bg-green-500/5',
    warning: 'border-yellow-500/30 bg-yellow-500/5',
    danger: 'border-red-500/30 bg-red-500/5'
  };

  return (
    <div className={`rounded-lg border p-4 ${variantStyles[variant]}`}>
      <div className="text-muted-foreground text-sm">{label}</div>
      <div className="mt-1 text-2xl">{value}</div>
    </div>
  );
}
