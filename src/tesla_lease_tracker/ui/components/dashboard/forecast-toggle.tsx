interface ForecastToggleProps {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}

const options = [
  { value: "linear", label: "Linear" },
  { value: "prophet", label: "Time Series" },
];

export function ForecastToggle({ value, onChange, disabled }: ForecastToggleProps) {
  return (
    <div className="glass rounded-xl glow-border p-3">
      <p className="text-xs text-muted-foreground mb-2 px-1">Forecast Model</p>
      <div className="flex gap-1 bg-background/50 rounded-lg p-1">
        {options.map((opt) => (
          <button
            key={opt.value}
            onClick={() => onChange(opt.value)}
            disabled={disabled}
            className={`flex-1 px-3 py-1.5 text-xs font-medium rounded-md transition-all ${
              value === opt.value
                ? "bg-primary/15 text-primary glow-border"
                : "text-muted-foreground hover:text-foreground"
            } disabled:opacity-50`}
          >
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  );
}
