'use client';

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';

interface ReviewDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  action: 'Approved' | 'Rejected' | null;
  onConfirm: () => void;
  loading?: boolean;
}

export function ReviewDialog({
  open,
  onOpenChange,
  action,
  onConfirm,
  loading,
}: ReviewDialogProps) {
  const isApprove = action === 'Approved';

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="border-white/[0.06] bg-[#0c1a2a]">
        <DialogHeader>
          <DialogTitle className="text-white">
            {isApprove ? 'Approve Learning Event' : 'Reject Learning Event'}
          </DialogTitle>
          <DialogDescription className="text-slate-400">
            {isApprove
              ? 'This will mark the event as approved and activate the proposed KB article.'
              : 'This will mark the event as rejected. The proposed article will remain as draft.'}
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            className="border-white/[0.06] text-slate-400"
          >
            Cancel
          </Button>
          <Button
            onClick={onConfirm}
            disabled={loading}
            className={
              isApprove
                ? 'bg-emerald-600 text-white hover:bg-emerald-700'
                : 'bg-red-600 text-white hover:bg-red-700'
            }
          >
            {loading ? 'Processing...' : isApprove ? 'Approve' : 'Reject'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
