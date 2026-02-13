import type { FallbackProps } from "react-error-boundary";
import { Button } from "@/components/ui/button";

function DisruptionIcon() {
  return (
    <svg
      viewBox="0 0 48 48"
      fill="none"
      className="w-12 h-12"
      aria-hidden="true"
    >
      {/* Broken hexagonal outline */}
      <path
        d="M24 4L41.3 14V34L24 44L6.7 34V14L24 4Z"
        stroke="rgba(248,113,113,0.3)"
        strokeWidth="1"
        fill="none"
      />
      {/* Gap/break in the circuit */}
      <path
        d="M24 4L41.3 14V26"
        stroke="var(--warning)"
        strokeWidth="1.5"
        strokeLinecap="round"
        className="animate-[glow-pulse_2s_ease-in-out_infinite]"
      />
      <path
        d="M6.7 26V14L24 4"
        stroke="var(--warning)"
        strokeWidth="1.5"
        strokeLinecap="round"
        className="animate-[glow-pulse_2s_ease-in-out_infinite_0.3s]"
        style={{ animationDelay: "0.3s" }}
      />
      {/* Center disruption mark */}
      <line
        x1="24" y1="16" x2="24" y2="26"
        stroke="var(--warning)"
        strokeWidth="2"
        strokeLinecap="round"
      />
      <circle cx="24" cy="32" r="1.5" fill="var(--warning)" />
    </svg>
  );
}

export function ErrorFallback({ error, resetErrorBoundary }: FallbackProps) {
  const errorMessage =
    error instanceof Error ? error.message : "An unexpected error occurred.";
  const timestamp = new Date().toISOString().replace("T", " ").slice(0, 19);

  return (
    <div className="flex items-center justify-center min-h-[60vh] animate-fade-up">
      {/* Red ambient glow */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div
          className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] rounded-full opacity-15 blur-[100px]"
          style={{ background: "radial-gradient(circle, #f87171 0%, transparent 70%)" }}
        />
      </div>

      <div
        className="relative glass rounded-2xl p-8 max-w-md w-full"
        style={{
          borderColor: "rgba(248,113,113,0.15)",
          boxShadow:
            "0 0 40px rgba(248,113,113,0.06), inset 0 1px 0 rgba(255,255,255,0.04)",
        }}
      >
        {/* Scanline overlay */}
        <div
          className="absolute inset-0 rounded-2xl pointer-events-none opacity-[0.03]"
          style={{
            backgroundImage:
              "repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(255,255,255,0.5) 2px, rgba(255,255,255,0.5) 3px)",
          }}
        />

        <div className="relative space-y-6">
          {/* Icon + status label */}
          <div className="flex items-start gap-4">
            <DisruptionIcon />
            <div>
              <p className="font-display text-xs font-semibold tracking-[0.2em] uppercase text-warning/80">
                System Fault
              </p>
              <h3 className="font-display text-lg font-bold text-foreground mt-1">
                Something went wrong
              </h3>
            </div>
          </div>

          {/* Diagnostic readout */}
          <div
            className="rounded-lg p-3 font-mono text-xs space-y-1"
            style={{
              background: "rgba(248,113,113,0.04)",
              border: "1px solid rgba(248,113,113,0.08)",
            }}
          >
            <div className="flex justify-between text-muted-foreground">
              <span>timestamp</span>
              <span>{timestamp}</span>
            </div>
            <div className="border-t border-white/[0.04] my-1" />
            <p className="text-warning/90 break-all leading-relaxed">
              {errorMessage}
            </p>
          </div>

          {/* Action */}
          <Button
            variant="outline"
            onClick={resetErrorBoundary}
            className="w-full glass font-semibold tracking-wide"
            style={{
              borderColor: "rgba(248,113,113,0.2)",
              color: "var(--warning)",
            }}
          >
            Retry
          </Button>
        </div>
      </div>
    </div>
  );
}
