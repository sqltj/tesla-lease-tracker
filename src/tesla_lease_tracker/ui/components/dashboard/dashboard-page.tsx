import { Suspense, useState } from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import {
  useGetLeaseSuspense,
  useGetDashboardSuspense,
  useGetMileageSuspense,
  useGetForecast,
} from "@/lib/api";
import { LeaseDialog } from "@/components/lease/lease-dialog";
import { MetricsCards } from "./metrics-cards";
import { MileageChart } from "./mileage-chart";
import { SyncButton } from "./sync-button";
import { ForecastToggle } from "./forecast-toggle";

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

  // Forecast is optional — only fetch if we have enough readings
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
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Dashboard</h2>
          <p className="text-muted-foreground">
            Tracking {lease.vin} &mdash;{" "}
            {lease.mileage_limit.toLocaleString()} mi limit
          </p>
        </div>
        <div className="flex items-center gap-2">
          <SyncButton />
          <LeaseDialog existingLease={lease} />
        </div>
      </div>

      {dashboard && <MetricsCards dashboard={dashboard} />}

      <MileageChart
        readings={readings}
        forecast={forecastData ?? null}
        mileageLimit={lease.mileage_limit}
      />

      {hasEnoughReadings && (
        <div className="flex items-center justify-center gap-3">
          <span className="text-sm text-muted-foreground">Forecast model:</span>
          <ForecastToggle value={forecastModel} onChange={setForecastModel} />
        </div>
      )}
    </div>
  );
}

function GetStarted() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-6">
      <div className="text-center space-y-2">
        <h2 className="text-3xl font-bold tracking-tight">
          Tesla Lease Mileage Tracker
        </h2>
        <p className="text-muted-foreground max-w-md">
          Track your lease mileage, forecast overage, and stay on budget.
          Configure your lease to get started.
        </p>
      </div>
      <LeaseDialog
        trigger={
          <Button size="lg" className="text-lg px-8">
            Get Started
          </Button>
        }
      />
    </div>
  );
}

function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-72" />
        </div>
        <Skeleton className="h-9 w-24" />
      </div>
      <div className="grid gap-4 md:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-32 rounded-xl" />
        ))}
      </div>
      <Skeleton className="h-80 rounded-xl" />
    </div>
  );
}

export function DashboardPage() {
  return (
    <Suspense fallback={<DashboardSkeleton />}>
      <DashboardContent />
    </Suspense>
  );
}
