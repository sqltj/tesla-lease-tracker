import type { FallbackProps } from "react-error-boundary";
import { Button } from "@/components/ui/button";

export function ErrorFallback({ error, resetErrorBoundary }: FallbackProps) {
  return (
    <div
      className="mx-auto mt-16 max-w-md glass rounded-xl p-8 text-center"
      style={{
        borderColor: "rgba(248,113,113,0.2)",
        boxShadow: "0 0 30px rgba(248,113,113,0.08)",
      }}
    >
      <div className="w-10 h-10 rounded-full bg-warning/10 flex items-center justify-center mx-auto mb-4">
        <span className="text-warning text-lg">!</span>
      </div>
      <h3 className="font-display text-lg font-semibold mb-2">Something went wrong</h3>
      <p className="text-sm text-muted-foreground mb-6 font-mono">
        {error instanceof Error ? error.message : "An unexpected error occurred."}
      </p>
      <Button
        variant="outline"
        onClick={resetErrorBoundary}
        className="glass border-white/10 hover:border-primary/30"
      >
        Try again
      </Button>
    </div>
  );
}
