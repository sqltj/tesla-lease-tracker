import { Suspense, useState } from "react";
import { ErrorBoundary } from "react-error-boundary";
import { useQueryErrorResetBoundary } from "@tanstack/react-query";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import {
  useGetLeaseSuspense,
  useGetDashboardSuspense,
  useGetMileageSuspense,
  useGetForecast,
} from "@/lib/api";
import { LeaseDialog } from "@/components/lease/lease-dialog";
import { ErrorFallback } from "./error-fallback";
import { ForecastToggle } from "./forecast-toggle";
import { HeroGauge } from "./hero-gauge";
import { MetricsCards } from "./metrics-cards";
import { MileageChart } from "./mileage-chart";
import { SyncButton } from "./sync-button";

function DashboardContent() {
  const { data: lease } = useGetLeaseSuspense({
    query: { select: (d) => d.data },
  });

  if (!lease) {
    return <GetStarted />;
  }

  return <DashboardWithData />;
}

function DashboardWithData() {
  const [forecastModel, setForecastModel] = useState("linear");

  const { data: lease } = useGetLeaseSuspense({
    query: { select: (d) => d.data },
  });
  const { data: dashboard } = useGetDashboardSuspense({
    query: { select: (d) => d.data },
  });
  const { data: readings } = useGetMileageSuspense({
    query: { select: (d) => d.data },
  });

  const hasEnoughReadings = readings.length >= 3;
  const { data: forecastData } = useGetForecast({
    params: { model: forecastModel },
    query: {
      enabled: hasEnoughReadings,
      select: (d) => d.data,
    },
  });

  if (!lease) return null;

  return (
    <div className="space-y-8">
      {/* Header row */}
      <div className="flex items-center justify-between animate-fade-up">
        <div>
          <h1 className="font-display text-xl font-semibold tracking-tight text-foreground">
            Mileage Tracker
          </h1>
          <p className="text-sm text-muted-foreground font-mono">
            {lease.vin} &mdash; {lease.mileage_limit.toLocaleString()} mi
          </p>
        </div>
        <div className="flex items-center gap-2">
          <SyncButton />
          <LeaseDialog existingLease={lease} />
        </div>
      </div>

      {/* Hero gauge */}
      {dashboard && (
        <HeroGauge
          milesUsed={dashboard.lease_miles_used}
          mileageLimit={lease.mileage_limit}
          dailyAverage={dashboard.daily_average}
          budgetDailyRate={dashboard.budget_daily_rate}
          daysRemaining={dashboard.days_remaining}
          overUnder={dashboard.over_under}
        />
      )}

      {/* Chart + Sidebar grid */}
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_300px] gap-6 animate-fade-up delay-300">
        <MileageChart
          readings={readings}
          forecast={forecastData ?? null}
          mileageLimit={lease.mileage_limit}
        />
        <aside className="space-y-4">
          {dashboard && <MetricsCards dashboard={dashboard} />}
          {hasEnoughReadings && (
            <ForecastToggle value={forecastModel} onChange={setForecastModel} />
          )}
        </aside>
      </div>
    </div>
  );
}

function GetStarted() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[70vh] animate-fade-up">
      {/* Ambient glow behind content */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div
          className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full opacity-20 blur-[120px]"
          style={{ background: "radial-gradient(circle, #38bdf8 0%, transparent 70%)" }}
        />
      </div>

      <div className="relative text-center space-y-4">
        <h2 className="font-display text-4xl sm:text-5xl font-bold tracking-tight text-foreground">
          Mileage Tracker
        </h2>
        <p className="text-muted-foreground max-w-md mx-auto text-base leading-relaxed">
          Track your Tesla lease mileage, forecast overage, and stay on budget.
        </p>
      </div>

      <div className="relative mt-8">
        <LeaseDialog
          trigger={
            <Button
              size="lg"
              className="text-base px-10 py-6 bg-primary hover:bg-primary/90 text-primary-foreground font-semibold rounded-xl shadow-[0_0_30px_rgba(56,189,248,0.2)] hover:shadow-[0_0_40px_rgba(56,189,248,0.3)] transition-all"
            >
              Get Started
            </Button>
          }
        />
      </div>
    </div>
  );
}

function DashboardSkeleton() {
  return (
    <div className="space-y-8">
      {/* Header skeleton */}
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <Skeleton className="h-6 w-40" />
          <Skeleton className="h-4 w-56" />
        </div>
        <Skeleton className="h-9 w-24" />
      </div>

      {/* Gauge skeleton */}
      <div className="flex justify-center">
        <Skeleton className="h-[280px] w-[280px] rounded-full" />
      </div>

      {/* Chart + sidebar skeleton */}
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_300px] gap-6">
        <Skeleton className="h-80 rounded-xl" />
        <div className="space-y-4">
          <Skeleton className="h-64 rounded-xl" />
          <Skeleton className="h-10 rounded-lg" />
        </div>
      </div>
    </div>
  );
}

export function DashboardPage() {
  const { reset } = useQueryErrorResetBoundary();

  return (
    <ErrorBoundary onReset={reset} FallbackComponent={ErrorFallback}>
      <Suspense fallback={<DashboardSkeleton />}>
        <DashboardContent />
      </Suspense>
    </ErrorBoundary>
  );
}
