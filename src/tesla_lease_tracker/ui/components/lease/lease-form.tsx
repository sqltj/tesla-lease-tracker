import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useSaveLease, getLeaseKey, getDashboardKey, type LeaseConfigOut } from "@/lib/api";

interface LeaseFormProps {
  existingLease?: LeaseConfigOut | null;
  onSuccess?: () => void;
}

export function LeaseForm({ existingLease, onSuccess }: LeaseFormProps) {
  const queryClient = useQueryClient();
  const [vin, setVin] = useState(existingLease?.vin ?? "");
  const [leaseStartDate, setLeaseStartDate] = useState(
    existingLease?.lease_start_date ?? ""
  );
  const [leaseEndDate, setLeaseEndDate] = useState(
    existingLease?.lease_end_date ?? ""
  );
  const [mileageLimit, setMileageLimit] = useState(
    existingLease?.mileage_limit?.toString() ?? ""
  );
  const [startOdometer, setStartOdometer] = useState(
    existingLease?.start_odometer?.toString() ?? ""
  );

  const mutation = useSaveLease({
    mutation: {
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: getLeaseKey() });
        queryClient.invalidateQueries({ queryKey: getDashboardKey() });
        toast.success("Lease configuration saved");
        onSuccess?.();
      },
      onError: (error) => {
        toast.error(
          `Failed to save: ${error instanceof Error ? error.message : "Unknown error"}`
        );
      },
    },
  });

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        mutation.mutate({
          vin,
          lease_start_date: leaseStartDate,
          lease_end_date: leaseEndDate,
          mileage_limit: Number(mileageLimit),
          start_odometer: Number(startOdometer),
        });
      }}
      className="space-y-4"
    >
      <div className="space-y-2">
        <Label htmlFor="vin">VIN</Label>
        <Input
          id="vin"
          placeholder="5YJ3E1EA..."
          value={vin}
          onChange={(e) => setVin(e.target.value)}
          required
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="lease-start">Lease Start</Label>
          <Input
            id="lease-start"
            type="date"
            value={leaseStartDate}
            onChange={(e) => setLeaseStartDate(e.target.value)}
            required
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="lease-end">Lease End</Label>
          <Input
            id="lease-end"
            type="date"
            value={leaseEndDate}
            onChange={(e) => setLeaseEndDate(e.target.value)}
            required
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="mileage-limit">Mileage Limit</Label>
          <Input
            id="mileage-limit"
            type="number"
            placeholder="36000"
            value={mileageLimit}
            onChange={(e) => setMileageLimit(e.target.value)}
            required
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="start-odometer">Start Odometer</Label>
          <Input
            id="start-odometer"
            type="number"
            step="0.1"
            placeholder="0"
            value={startOdometer}
            onChange={(e) => setStartOdometer(e.target.value)}
            required
          />
        </div>
      </div>

      <Button type="submit" className="w-full bg-primary hover:bg-primary/90 text-primary-foreground font-medium" disabled={mutation.isPending}>
        {mutation.isPending ? (
          <>
            <span className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-primary-foreground border-t-transparent" />
            Saving...
          </>
        ) : (
          "Save Lease Configuration"
        )}
      </Button>

      {mutation.isError && (
        <p className="text-sm text-destructive">
          Failed to save: {mutation.error.message}
        </p>
      )}
    </form>
  );
}
