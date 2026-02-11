import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { DashboardOut } from "@/lib/api";

interface MetricsCardsProps {
  dashboard: DashboardOut;
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

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Lease Miles Used
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {Math.round(lease_miles_used).toLocaleString()}
          </div>
          <p className="text-xs text-muted-foreground">
            of {mileage_limit.toLocaleString()} mi limit
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Daily Average
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className={`text-2xl font-bold ${isOverPace ? "text-red-500" : "text-green-500"}`}>
            {daily_average} mi/day
          </div>
          <p className="text-xs text-muted-foreground">
            budget: {budget_daily_rate} mi/day
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Days Remaining
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{days_remaining}</div>
          <p className="text-xs text-muted-foreground">
            of {total_lease_days} total
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Projected End
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className={`text-2xl font-bold ${isOverProjected ? "text-red-500" : "text-green-500"}`}>
            {isOverProjected ? "+" : ""}
            {Math.round(over_under).toLocaleString()} mi
          </div>
          <p className="text-xs text-muted-foreground">
            {isOverProjected ? "over" : "under"} limit ({Math.round(projected_end_miles).toLocaleString()} mi projected)
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
