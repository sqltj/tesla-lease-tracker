import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { ErrorFallback } from "../error-fallback";

describe("ErrorFallback", () => {
  it("renders error message from Error object", () => {
    render(
      <ErrorFallback
        error={new Error("Test error message")}
        resetErrorBoundary={vi.fn()}
      />
    );
    expect(screen.getByText("Test error message")).toBeInTheDocument();
  });

  it("renders fallback message for non-Error objects", () => {
    render(
      <ErrorFallback
        error={"some string error" as unknown as Error}
        resetErrorBoundary={vi.fn()}
      />
    );
    expect(screen.getByText("An unexpected error occurred.")).toBeInTheDocument();
  });

  it("renders System Fault label", () => {
    render(
      <ErrorFallback
        error={new Error("fail")}
        resetErrorBoundary={vi.fn()}
      />
    );
    expect(screen.getByText("System Fault")).toBeInTheDocument();
  });

  it("renders Something went wrong heading", () => {
    render(
      <ErrorFallback
        error={new Error("fail")}
        resetErrorBoundary={vi.fn()}
      />
    );
    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
  });

  it("renders timestamp", () => {
    render(
      <ErrorFallback
        error={new Error("fail")}
        resetErrorBoundary={vi.fn()}
      />
    );
    expect(screen.getByText("timestamp")).toBeInTheDocument();
  });

  it("calls resetErrorBoundary when retry clicked", async () => {
    const resetFn = vi.fn();
    render(
      <ErrorFallback error={new Error("fail")} resetErrorBoundary={resetFn} />
    );
    await userEvent.click(screen.getByRole("button", { name: /retry/i }));
    expect(resetFn).toHaveBeenCalledOnce();
  });
});
