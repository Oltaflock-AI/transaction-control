import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { format } from "date-fns";
import { CalendarIcon, Plus } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Calendar } from "@/components/ui/calendar";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { useToast } from "@/hooks/use-toast";
import { MOCK_TRANSACTIONS, MOCK_HEALTH } from "@/lib/mock-data";
import type { Transaction, HealthScore } from "@/lib/types";

interface CreateTransactionDialogProps {
  onCreated?: (tx: Transaction) => void;
}

const CreateTransactionDialog = ({ onCreated }: CreateTransactionDialogProps) => {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [propertyAddress, setPropertyAddress] = useState("");
  const [closeDate, setCloseDate] = useState<Date>();
  const { toast } = useToast();
  const navigate = useNavigate();

  const resetForm = () => {
    setTitle("");
    setDescription("");
    setPropertyAddress("");
    setCloseDate(undefined);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!title.trim()) {
      toast({ title: "Title is required", variant: "destructive" });
      return;
    }

    setLoading(true);

    // Simulate API call — will be replaced with createTransaction() from api.ts
    setTimeout(() => {
      const now = new Date().toISOString();
      const newTx: Transaction = {
        id: `t${Date.now()}`,
        org_id: "org-1",
        title: title.trim(),
        description: description.trim() || undefined,
        status: "draft",
        property_address: propertyAddress.trim() || undefined,
        close_date: closeDate ? format(closeDate, "yyyy-MM-dd") : undefined,
        health_score: "GREEN",
        created_at: now,
        updated_at: now,
      };

      // Add to mock data arrays (in-memory only)
      MOCK_TRANSACTIONS.push(newTx);
      (MOCK_HEALTH as Record<string, HealthScore>)[newTx.id] = {
        status: "GREEN",
        reasons: [],
      };

      toast({ title: "Transaction created", description: newTx.title });
      onCreated?.(newTx);
      setLoading(false);
      setOpen(false);
      resetForm();
      navigate(`/dashboard/transactions/${newTx.id}`);
    }, 500);
  };

  return (
    <Dialog open={open} onOpenChange={(v) => { setOpen(v); if (!v) resetForm(); }}>
      <DialogTrigger asChild>
        <Button>
          <Plus className="h-4 w-4 mr-2" />
          New Transaction
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[520px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Create Transaction</DialogTitle>
            <DialogDescription>
              Add a new real-estate deal. Timeline and tasks will be auto-generated.
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="tx-title">Title *</Label>
              <Input
                id="tx-title"
                placeholder="e.g. 123 Main St Sale"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                maxLength={200}
                autoFocus
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="tx-desc">Description</Label>
              <Textarea
                id="tx-desc"
                placeholder="Brief deal description…"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                maxLength={1000}
                rows={3}
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="tx-address">Property Address</Label>
              <Input
                id="tx-address"
                placeholder="e.g. 123 Main St, Austin, TX 78701"
                value={propertyAddress}
                onChange={(e) => setPropertyAddress(e.target.value)}
                maxLength={300}
              />
            </div>

            <div className="grid gap-2">
              <Label>Close Date</Label>
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    className={cn(
                      "w-full justify-start text-left font-normal",
                      !closeDate && "text-muted-foreground"
                    )}
                  >
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {closeDate ? format(closeDate, "PPP") : "Pick a date"}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="start">
                  <Calendar
                    mode="single"
                    selected={closeDate}
                    onSelect={setCloseDate}
                    disabled={(date) => date < new Date()}
                    initialFocus
                    className={cn("p-3 pointer-events-auto")}
                  />
                </PopoverContent>
              </Popover>
            </div>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? "Creating…" : "Create Transaction"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export default CreateTransactionDialog;
