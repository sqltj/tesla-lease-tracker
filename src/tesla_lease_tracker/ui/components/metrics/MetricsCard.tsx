import { Suspense } from "react";
import { ErrorBoundary } from "react-error-boundary";
import { useQueryErrorResetBoundary } from "@tanstack/react-query";
import { useGetMetricsSuspense } from "@/lib/api";
import { Skeleton } from "@/components/ui/skeleton";

function MetricsCardContent() {
  const { data: metrics } = useGetMetricsSuspense({
    query: { select: (d) => d.data },
  });

  const errorPct = (metrics.error_rate * 100).toFixed(1);
  const hasErrors = metrics.error_rate > 0;
  const hasWarnings = metrics.data_quality_warnings > 0;

  const rows = [
    {
      label: "Requests",
      value: metrics.request_count.toLocaleString(),
      sub: `${metrics.window_size} in window`,
      warn: false,
    },
    {
      label: "Error Rate",
      value: `${errorPct}%`,
      sub: `${metrics.error_count} errors`,
      warn: hasErrors,
    },
    {
      label: "Latency p95",
      value: `${metrics.latency_p95}ms`,
      sub: `p50: ${metrics.latency_p50}ms`,
      warn: metrics.latency_p95 > 1000,
    },
    {
      label: "Quality Warnings",
      value: metrics.data_quality_warnings.toString(),
      sub: "data validation",
      warn: hasWarnings,
    },
  ];

  return (
    <div className="glass rounded-xl p-4 space-y-0 glow-border">
      <p className="text-xs text-muted-foreground font-mono pb-2 border-b border-white/5">
        API Metrics
      </p>
      {rows.map((row, i) => (
        <div
          key={row.label}
          className={`flex items-center justify-between py-3 ${
            i < rows.length - 1 ? "border-b border-white/5" : ""
          }`}
        >
          <div className="flex items-center gap-2.5">
            <span
              className={`w-1.5 h-1.5 rounded-full ${row.warn ? "bg-warning" : "bg-muted-foreground/40"}`}
            />
            <span className="text-sm text-muted-foreground">{row.label}</span>
          </div>
          <div className="text-right">
            <span className="font-mono text-sm font-medium text-foreground">
              {row.value}
            </span>
            <p className="text-xs text-muted-foreground">{row.sub}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

function MetricsCardSkeleton() {
  return <Skeleton className="h-[188px] rounded-xl" />;
}

export function MetricsCard() {
  const { reset } = useQueryErrorResetBoundary();
  return (
    <ErrorBoundary onReset={reset} fallback={null}>
      <Suspense fallback={<MetricsCardSkeleton />}>
        <MetricsCardContent />
      </Suspense>
    </ErrorBoundary>
  );
}
