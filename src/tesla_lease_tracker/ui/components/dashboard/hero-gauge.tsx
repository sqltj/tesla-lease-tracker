interface HeroGaugeProps {
  milesUsed: number;
  mileageLimit: number;
  dailyAverage: number;
  budgetDailyRate: number;
  daysRemaining: number;
  overUnder: number;
}

const SIZE = 280;
const STROKE_WIDTH = 12;
const RADIUS = (SIZE - STROKE_WIDTH) / 2;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;
const ARC_LENGTH = CIRCUMFERENCE * 0.75;

export function HeroGauge({
  milesUsed,
  mileageLimit,
  dailyAverage,
  budgetDailyRate,
  daysRemaining,
  overUnder,
}: HeroGaugeProps) {
  const isOver = overUnder > 0;
  const pct = Math.min(milesUsed / mileageLimit, 1.2);
  const offset = ARC_LENGTH - ARC_LENGTH * Math.min(pct, 1);

  const ringColor = isOver ? "#f87171" : "#38bdf8";
  const glowColor = isOver
    ? "rgba(248,113,113,0.3)"
    : "rgba(56,189,248,0.3)";

  const isOverPace = dailyAverage > budgetDailyRate;

  return (
    <div className="flex flex-col items-center gap-4 animate-fade-up delay-100">
      <div
        className="relative w-[240px] h-[240px] sm:w-[280px] sm:h-[280px]"
      >
        <svg
          viewBox={`0 0 ${SIZE} ${SIZE}`}
          className="w-full h-full -rotate-[135deg]"
        >
          {/* Background track */}
          <circle
            cx={SIZE / 2}
            cy={SIZE / 2}
            r={RADIUS}
            fill="none"
            stroke="rgba(255,255,255,0.06)"
            strokeWidth={STROKE_WIDTH}
            strokeDasharray={`${ARC_LENGTH} ${CIRCUMFERENCE}`}
            strokeLinecap="round"
          />
          {/* Progress arc */}
          <circle
            cx={SIZE / 2}
            cy={SIZE / 2}
            r={RADIUS}
            fill="none"
            stroke={ringColor}
            strokeWidth={STROKE_WIDTH}
            strokeDasharray={`${ARC_LENGTH} ${CIRCUMFERENCE}`}
            strokeDashoffset={offset}
            strokeLinecap="round"
            style={
              {
                filter: `drop-shadow(0 0 8px ${glowColor})`,
                "--gauge-circumference": `${ARC_LENGTH}`,
                "--gauge-offset": `${offset}`,
              } as React.CSSProperties
            }
            className="animate-gauge-fill"
          />
        </svg>

        {/* Center content */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span
            className="font-mono text-4xl font-medium tracking-tight"
            style={{ color: ringColor }}
          >
            {isOver ? "+" : ""}
            {Math.abs(Math.round(overUnder)).toLocaleString()}
          </span>
          <span className="text-sm text-muted-foreground mt-1">
            {isOver ? "miles over budget" : "miles remaining"}
          </span>
        </div>
      </div>

      {/* Sub-stats below gauge */}
      <div className="flex items-center gap-6 text-sm text-muted-foreground">
        <div className="flex items-center gap-2">
          <span
            className={`inline-block w-1.5 h-1.5 rounded-full ${
              isOverPace ? "bg-warning" : "bg-good"
            }`}
          />
          <span className="font-mono">{dailyAverage}</span>
          <span>mi/day avg</span>
        </div>
        <div className="text-white/10">|</div>
        <div>
          <span className="font-mono">{daysRemaining}</span>
          <span> days left</span>
        </div>
      </div>
    </div>
  );
}
