import type { DashboardOut } from "@/lib/api";

interface MetricsCardsProps {
  dashboard: DashboardOut;
}

type MetricStatus = "good" | "warning" | "neutral";

interface Metric {
  label: string;
  value: string;
  sub: string;
  status: MetricStatus;
}

function statusDotClass(status: MetricStatus): string {
  if (status === "good") return "bg-good";
  if (status === "warning") return "bg-warning";
  return "bg-muted-foreground/40";
}

export function MetricsCards({ dashboard }: MetricsCardsProps) {
  const {
    lease_miles_used,
    mileage_limit,
    daily_average,
    budget_daily_rate,
    days_remaining,
    total_lease_days,
    projected_end_miles,
    over_under,
  } = dashboard;

  const isOverPace = daily_average > budget_daily_rate;
  const isOverProjected = over_under > 0;

  const metrics: Metric[] = [
    {
      label: "Miles Used",
      value: `${Math.round(lease_miles_used).toLocaleString()}`,
      sub: `of ${mileage_limit.toLocaleString()} limit`,
      status: "neutral",
    },
    {
      label: "Daily Average",
      value: `${daily_average} mi/day`,
      sub: `budget: ${budget_daily_rate} mi/day`,
      status: isOverPace ? "warning" : "good",
    },
    {
      label: "Days Remaining",
      value: `${days_remaining}`,
      sub: `of ${total_lease_days} total`,
      status: "neutral",
    },
    {
      label: "Projected End",
      value: `${isOverProjected ? "+" : ""}${Math.round(over_under).toLocaleString()} mi`,
      sub: `${Math.round(projected_end_miles).toLocaleString()} mi projected`,
      status: isOverProjected ? "warning" : "good",
    },
  ];

  return (
    <div className="glass rounded-xl p-4 space-y-0 glow-border">
      {metrics.map((m, i) => (
        <div
          key={m.label}
          className={`flex items-center justify-between py-3 animate-fade-up ${
            i < metrics.length - 1 ? "border-b border-white/5" : ""
          }`}
          style={{ animationDelay: `${i * 80}ms` }}
        >
          <div className="flex items-center gap-2.5">
            <span
              className={`w-1.5 h-1.5 rounded-full ${statusDotClass(m.status)}`}
            />
            <span className="text-sm text-muted-foreground">{m.label}</span>
          </div>
          <div className="text-right">
            <span className="font-mono text-sm font-medium text-foreground">
              {m.value}
            </span>
            <p className="text-xs text-muted-foreground">{m.sub}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
