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
        toast.error(`Sync failed: ${error.message}`);
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
    >
      {mutation.isPending ? (
        <>
          <span className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
          Syncing...
        </>
      ) : (
        "Sync Mileage"
      )}
    </Button>
  );
}
