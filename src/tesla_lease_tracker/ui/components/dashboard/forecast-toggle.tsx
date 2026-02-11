import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";

interface ForecastToggleProps {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}

export function ForecastToggle({ value, onChange, disabled }: ForecastToggleProps) {
  return (
    <ToggleGroup
      type="single"
      value={value}
      onValueChange={(v) => {
        if (v) onChange(v);
      }}
      disabled={disabled}
    >
      <ToggleGroupItem value="linear" aria-label="Linear forecast">
        Linear
      </ToggleGroupItem>
      <ToggleGroupItem value="prophet" aria-label="Time series forecast">
        Time Series
      </ToggleGroupItem>
    </ToggleGroup>
  );
}
