/** Reusable KPI card component for dashboard metrics. */

interface MetricCardProps {
  label: string;
  value: string | number;
  icon?: string;
  color?: "brand" | "safe" | "warning" | "danger";
  isLoading?: boolean;
}

export function MetricCard({
  label,
  value,
  icon = "📊",
  color = "brand",
  isLoading = false,
}: MetricCardProps) {
  const borderColors: Record<string, string> = {
    brand: "border-brand",
    safe: "border-safe",
    warning: "border-warning",
    danger: "border-danger",
  };

  const accentBg: Record<string, string> = {
    brand: "bg-brand/10 text-brand dark:bg-brand/20",
    safe: "bg-safe/10 text-safe dark:bg-safe/20",
    warning: "bg-warning/10 text-warning dark:bg-warning/20",
    danger: "bg-danger/10 text-danger dark:bg-danger/20",
  };

  return (
    <div
      className={`card flex items-center gap-4 border-l-4 ${borderColors[color]} p-4`}
    >
      {/* Icon */}
      <div
        className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-lg text-xl ${accentBg[color]}`}
      >
        {icon}
      </div>

      {/* Content */}
      <div className="min-w-0 flex-1">
        <p className="truncate text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
          {label}
        </p>
        {isLoading ? (
          <div className="mt-1.5 h-7 w-20 animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
        ) : (
          <p className="mt-0.5 text-2xl font-bold text-slate-800 dark:text-white">
            {value}
          </p>
        )}
      </div>
    </div>
  );
}
