import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  useSyncMileage,
  getMileageKey,
  getDashboardKey,
} from "@/lib/api";

export function SyncButton() {
  const queryClient = useQueryClient();

  const mutation = useSyncMileage({
    mutation: {
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: getMileageKey() });
        queryClient.invalidateQueries({ queryKey: getDashboardKey() });
        toast.success("Mileage synced successfully");
      },
      onError: (error) => {
        toast.error(`Sync failed: ${error.message}`, {
          action: {
            label: "Retry",
            onClick: () => mutation.mutate(),
          },
          duration: 10000,
        });
      },
    },
  });

  const handleSync = () => {
    toast.warning("This will wake your vehicle.", {
      action: {
        label: "Sync anyway",
        onClick: () => mutation.mutate(),
      },
      duration: 8000,
    });
  };

  return (
    <Button
      variant="outline"
      size="sm"
      onClick={handleSync}
      disabled={mutation.isPending}
      className="glass border-white/10 hover:border-primary/30 hover:shadow-[0_0_15px_rgba(56,189,248,0.1)] transition-all"
    >
      {mutation.isPending ? (
        <>
          <span className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          <span className="font-mono text-xs">Syncing</span>
        </>
      ) : (
        <span className="text-xs">Sync Mileage</span>
      )}
    </Button>
  );
}
