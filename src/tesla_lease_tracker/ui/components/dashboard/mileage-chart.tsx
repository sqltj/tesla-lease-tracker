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
} from "recharts";
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

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="glass rounded-lg px-3 py-2 glow-border text-xs">
      <p className="font-mono text-muted-foreground mb-1">
        {new Date(String(label) + "T00:00:00").toLocaleDateString("en-US", {
          month: "short",
          day: "numeric",
          year: "numeric",
        })}
      </p>
      {payload.map((entry: any) => (
        <p key={entry.dataKey} className="font-mono" style={{ color: entry.color }}>
          {entry.name}: {Number(entry.value).toLocaleString()} mi
        </p>
      ))}
    </div>
  );
}

export function MileageChart({ readings, forecast, mileageLimit }: MileageChartProps) {
  const chartData: ChartPoint[] = [];

  for (const r of readings) {
    chartData.push({
      date: new Date(r.timestamp).toISOString().slice(0, 10),
      actual: Math.round(r.lease_miles),
    });
  }

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

  chartData.sort((a, b) => a.date.localeCompare(b.date));
  const today = new Date().toISOString().slice(0, 10);

  if (chartData.length === 0) {
    return (
      <div className="glass rounded-xl glow-border h-[420px] flex items-center justify-center text-muted-foreground text-sm">
        Sync mileage data to see your chart
      </div>
    );
  }

  return (
    <div className="glass rounded-xl glow-border p-4">
      <ResponsiveContainer width="100%" height={420}>
        <ComposedChart data={chartData} margin={{ top: 10, right: 20, bottom: 10, left: 10 }}>
          <defs>
            <linearGradient id="actualGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#38bdf8" stopOpacity={0.2} />
              <stop offset="100%" stopColor="#38bdf8" stopOpacity={0} />
            </linearGradient>
          </defs>

          <CartesianGrid stroke="rgba(255,255,255,0.04)" strokeDasharray="none" />

          <XAxis
            dataKey="date"
            tick={{ fontSize: 11, fill: "#71717a", fontFamily: "JetBrains Mono" }}
            tickFormatter={(v: string) => {
              const d = new Date(v + "T00:00:00");
              return d.toLocaleDateString("en-US", { month: "short", year: "2-digit" });
            }}
            stroke="rgba(255,255,255,0.06)"
            tickLine={false}
          />

          <YAxis
            tick={{ fontSize: 11, fill: "#71717a", fontFamily: "JetBrains Mono" }}
            tickFormatter={(v: number) => `${(v / 1000).toFixed(0)}k`}
            stroke="rgba(255,255,255,0.06)"
            tickLine={false}
            axisLine={false}
          />

          <Tooltip content={<CustomTooltip />} />

          {/* Gradient fill under actual line */}
          <Area
            type="monotone"
            dataKey="actual"
            fill="url(#actualGradient)"
            stroke="none"
            connectNulls={false}
            legendType="none"
          />

          {/* Confidence interval */}
          {forecast && forecast.points.some((p) => p.lower_bound != null) && (
            <Area
              dataKey="confidence"
              fill="rgba(34,211,238,0.08)"
              stroke="none"
              legendType="none"
            />
          )}

          {/* Mileage limit reference line */}
          <ReferenceLine
            y={mileageLimit}
            stroke="#f87171"
            strokeDasharray="8 4"
            strokeOpacity={0.6}
            label={{ value: "Limit", position: "right", fontSize: 11, fill: "#f87171" }}
          />

          {/* Today marker */}
          <ReferenceLine
            x={today}
            stroke="rgba(255,255,255,0.2)"
            strokeDasharray="4 4"
            label={{ value: "Today", position: "top", fontSize: 10, fill: "#71717a" }}
          />

          {/* Actual mileage line */}
          <Line
            type="monotone"
            dataKey="actual"
            stroke="#38bdf8"
            strokeWidth={2.5}
            dot={false}
            name="Actual"
            connectNulls={false}
            animationDuration={1500}
            animationEasing="ease-out"
          />

          {/* Forecast line */}
          <Line
            type="monotone"
            dataKey="forecast"
            stroke="#22d3ee"
            strokeWidth={2}
            strokeDasharray="6 3"
            dot={false}
            name="Forecast"
            connectNulls={false}
            animationDuration={1500}
            animationEasing="ease-out"
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
