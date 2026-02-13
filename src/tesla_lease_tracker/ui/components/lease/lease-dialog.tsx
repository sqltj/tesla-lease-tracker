import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { LeaseForm } from "./lease-form";
import type { LeaseConfigOut } from "@/lib/api";

interface LeaseDialogProps {
  existingLease?: LeaseConfigOut | null;
  onSaved?: () => void;
  trigger?: React.ReactNode;
}

export function LeaseDialog({ existingLease, onSaved, trigger }: LeaseDialogProps) {
  const [open, setOpen] = useState(false);

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {trigger || (
          <Button variant={existingLease ? "outline" : "default"} size="sm">
            {existingLease ? "Edit Lease" : "Configure Lease"}
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="sm:max-w-md glass glow-border border-white/8">
        <DialogHeader>
          <DialogTitle className="font-display">
            {existingLease ? "Edit Lease Configuration" : "Set Up Your Lease"}
          </DialogTitle>
        </DialogHeader>
        <LeaseForm
          existingLease={existingLease}
          onSuccess={() => {
            setOpen(false);
            onSaved?.();
          }}
        />
      </DialogContent>
    </Dialog>
  );
}
