import {
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { MileageReadingOut, ForecastOut } from "@/lib/api";

interface MileageChartProps {
  readings: MileageReadingOut[];
  forecast?: ForecastOut | null;
  mileageLimit: number;
}

interface ChartPoint {
  date: string;
  actual?: number;
  forecast?: number;
  lower?: number;
  upper?: number;
  confidence?: [number, number];
}

export function MileageChart({ readings, forecast, mileageLimit }: MileageChartProps) {
  const chartData: ChartPoint[] = [];

  // Historical readings
  for (const r of readings) {
    chartData.push({
      date: new Date(r.timestamp).toISOString().slice(0, 10),
      actual: Math.round(r.lease_miles),
    });
  }

  // Forecast points
  if (forecast) {
    for (const p of forecast.points) {
      const existing = chartData.find((d) => d.date === p.date);
      if (existing) {
        existing.forecast = Math.round(p.predicted_miles);
        if (p.lower_bound != null && p.upper_bound != null) {
          existing.confidence = [Math.round(p.lower_bound), Math.round(p.upper_bound)];
        }
      } else {
        chartData.push({
          date: p.date,
          forecast: Math.round(p.predicted_miles),
          confidence:
            p.lower_bound != null && p.upper_bound != null
              ? [Math.round(p.lower_bound), Math.round(p.upper_bound)]
              : undefined,
        });
      }
    }
  }

  // Sort by date
  chartData.sort((a, b) => a.date.localeCompare(b.date));

  const today = new Date().toISOString().slice(0, 10);

  if (chartData.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Mileage Over Time</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-80 flex items-center justify-center text-muted-foreground">
            Sync mileage data to see your chart
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Mileage Over Time</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={350}>
          <ComposedChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 12 }}
              tickFormatter={(v: string) => {
                const d = new Date(v + "T00:00:00");
                return d.toLocaleDateString("en-US", { month: "short", year: "2-digit" });
              }}
            />
            <YAxis
              tick={{ fontSize: 12 }}
              tickFormatter={(v: number) => `${(v / 1000).toFixed(0)}k`}
            />
            <Tooltip
              labelFormatter={(v) => new Date(String(v) + "T00:00:00").toLocaleDateString()}
              formatter={(value, name) => [
                `${Number(value).toLocaleString()} mi`,
                name === "actual" ? "Actual" : name === "forecast" ? "Forecast" : String(name),
              ]}
            />
            <Legend />

            {/* Confidence interval (shaded area) */}
            {forecast && forecast.points.some((p) => p.lower_bound != null) && (
              <Area
                dataKey="confidence"
                fill="hsl(var(--primary) / 0.1)"
                stroke="none"
                name="Confidence"
                legendType="none"
              />
            )}

            {/* Mileage limit reference line */}
            <ReferenceLine
              y={mileageLimit}
              stroke="hsl(0, 84%, 60%)"
              strokeDasharray="8 4"
              label={{ value: "Limit", position: "right", fontSize: 12 }}
            />

            {/* Today marker */}
            <ReferenceLine
              x={today}
              stroke="hsl(var(--muted-foreground))"
              strokeDasharray="4 4"
              label={{ value: "Today", position: "top", fontSize: 11 }}
            />

            {/* Actual mileage line */}
            <Line
              type="monotone"
              dataKey="actual"
              stroke="hsl(var(--primary))"
              strokeWidth={2}
              dot={false}
              name="Actual"
              connectNulls={false}
            />

            {/* Forecast line */}
            <Line
              type="monotone"
              dataKey="forecast"
              stroke="hsl(var(--primary))"
              strokeWidth={2}
              strokeDasharray="6 3"
              dot={false}
              name="Forecast"
              connectNulls={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
