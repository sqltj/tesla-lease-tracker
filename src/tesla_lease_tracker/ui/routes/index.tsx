import { createFileRoute } from "@tanstack/react-router";
import Navbar from "@/components/apx/navbar";
import { DashboardPage } from "@/components/dashboard/dashboard-page";

export const Route = createFileRoute("/")({
  component: () => <Index />,
});

function Index() {
  return (
    <div className="min-h-screen flex flex-col bg-background bg-dot-grid">
      <Navbar />
      <main className="flex-1 w-full max-w-6xl mx-auto px-4 sm:px-6 py-8">
        <DashboardPage />
      </main>
    </div>
  );
}
