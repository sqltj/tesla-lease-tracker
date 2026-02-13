import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { MetricsCards } from "../metrics-cards";

const baseDashboard = {
  lease_miles_used: 12500,
  mileage_limit: 36000,
  daily_average: 34.2,
  budget_daily_rate: 32.9,
  days_remaining: 547,
  total_lease_days: 1096,
  projected_end_miles: 37500,
  over_under: 1500,
  last_sync: "2024-06-15T10:30:00Z",
  last_odometer: 22500,
};

describe("MetricsCards", () => {
  it("renders all four metric labels", () => {
    render(<MetricsCards dashboard={baseDashboard} />);
    expect(screen.getByText("Miles Used")).toBeInTheDocument();
    expect(screen.getByText("Daily Average")).toBeInTheDocument();
    expect(screen.getByText("Days Remaining")).toBeInTheDocument();
    expect(screen.getByText("Projected End")).toBeInTheDocument();
  });

  it("displays formatted miles used", () => {
    render(<MetricsCards dashboard={baseDashboard} />);
    expect(screen.getByText("12,500")).toBeInTheDocument();
  });

  it("displays daily average with unit", () => {
    render(<MetricsCards dashboard={baseDashboard} />);
    expect(screen.getByText("34.2 mi/day")).toBeInTheDocument();
  });

  it("displays days remaining", () => {
    render(<MetricsCards dashboard={baseDashboard} />);
    expect(screen.getByText("547")).toBeInTheDocument();
  });

  it("shows positive over/under with + prefix", () => {
    render(<MetricsCards dashboard={baseDashboard} />);
    expect(screen.getByText("+1,500 mi")).toBeInTheDocument();
  });

  it("shows negative over/under without + prefix", () => {
    render(
      <MetricsCards dashboard={{ ...baseDashboard, over_under: -2000, projected_end_miles: 34000 }} />
    );
    expect(screen.getByText("-2,000 mi")).toBeInTheDocument();
  });

  it("handles zero values", () => {
    render(
      <MetricsCards
        dashboard={{
          ...baseDashboard,
          lease_miles_used: 0,
          daily_average: 0,
          days_remaining: 0,
          over_under: 0,
          projected_end_miles: 0,
        }}
      />
    );
    expect(screen.getByText("0 mi/day")).toBeInTheDocument();
  });
});
