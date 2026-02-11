import { createFileRoute } from "@tanstack/react-router";
import Navbar from "@/components/apx/navbar";
import { DashboardPage } from "@/components/dashboard/dashboard-page";

export const Route = createFileRoute("/")({
  component: () => <Index />,
});

function Index() {
  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Navbar />
      <main className="flex-1 container mx-auto px-4 py-6">
        <DashboardPage />
      </main>
    </div>
  );
}
