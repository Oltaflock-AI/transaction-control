import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Plus } from "lucide-react";
import { MOCK_USERS } from "@/lib/mock-data";
import type { Task, TaskSeverity } from "@/lib/types";
import { useToast } from "@/hooks/use-toast";

interface CreateTaskDialogProps {
  transactionId: string;
  transactionTitle: string;
  onTaskCreated: (task: Task) => void;
}

const CreateTaskDialog = ({ transactionId, transactionTitle, onTaskCreated }: CreateTaskDialogProps) => {
  const [open, setOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [severity, setSeverity] = useState<TaskSeverity>("medium");
  const [dueAt, setDueAt] = useState("");
  const [assigneeId, setAssigneeId] = useState("");
  const [category, setCategory] = useState("");
  const { toast } = useToast();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    const newTask: Task = {
      id: `task-${Date.now()}`,
      transaction_id: transactionId,
      title: title.trim(),
      description: description.trim() || undefined,
      status: "todo",
      assignee_id: assigneeId || undefined,
      due_at: dueAt ? new Date(dueAt).toISOString() : undefined,
      severity,
      category: category.trim() || undefined,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      transaction_title: transactionTitle,
    };

    onTaskCreated(newTask);
    toast({ title: "Task created", description: `"${title}" added successfully.` });
    setTitle("");
    setDescription("");
    setSeverity("medium");
    setDueAt("");
    setAssigneeId("");
    setCategory("");
    setOpen(false);
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm" variant="outline">
          <Plus className="h-4 w-4 mr-1" /> Add Task
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Create Task</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="task-title">Title *</Label>
            <Input id="task-title" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="e.g. Schedule home inspection" required />
          </div>
          <div className="space-y-2">
            <Label htmlFor="task-desc">Description</Label>
            <Textarea id="task-desc" value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Optional details..." rows={2} />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Severity</Label>
              <Select value={severity} onValueChange={(v) => setSeverity(v as TaskSeverity)}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="low">Low</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                  <SelectItem value="critical">Critical</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="task-category">Category</Label>
              <Input id="task-category" value={category} onChange={(e) => setCategory(e.target.value)} placeholder="e.g. Inspection" />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="task-due">Due Date</Label>
              <Input id="task-due" type="date" value={dueAt} onChange={(e) => setDueAt(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label>Assign To</Label>
              <Select value={assigneeId} onValueChange={setAssigneeId}>
                <SelectTrigger><SelectValue placeholder="Unassigned" /></SelectTrigger>
                <SelectContent>
                  {MOCK_USERS.map((u) => (
                    <SelectItem key={u.id} value={u.id}>{u.full_name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
            <Button type="submit">Create Task</Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export default CreateTaskDialog;
