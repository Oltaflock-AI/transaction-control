import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getMyTasks, updateTaskStatus } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { useToast } from "@/hooks/use-toast";
import type { Task, TaskStatus } from "@/lib/types";
import { CheckCircle2 } from "lucide-react";

const nextStatus: Record<string, TaskStatus> = {
  todo: "in_progress",
  in_progress: "done",
  done: "todo",
  overdue: "in_progress",
};

const statusStyle: Record<string, string> = {
  done: "bg-success/15 text-success border-success/30",
  in_progress: "bg-warning/15 text-warning border-warning/30",
  todo: "bg-muted text-muted-foreground",
  overdue: "bg-destructive/15 text-destructive border-destructive/30",
};

const severityStyle: Record<string, string> = {
  critical: "bg-destructive/15 text-destructive",
  high: "bg-warning/15 text-warning",
  medium: "bg-muted text-muted-foreground",
  low: "bg-accent text-accent-foreground",
};

const TasksPage = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const [confirmTask, setConfirmTask] = useState<Task | null>(null);

  const { data: myTasks, isLoading } = useQuery({
    queryKey: ["myTasks"],
    queryFn: getMyTasks,
  });

  const mutation = useMutation({
    mutationFn: ({ taskId, status }: { taskId: string, status: TaskStatus }) => updateTaskStatus(taskId, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["myTasks"] });
    },
    onError: (err: any) => toast({ title: "Failed to update status", description: err.message, variant: "destructive" })
  });

  const confirmToggleStatus = () => {
    if (confirmTask) {
      mutation.mutate({ taskId: confirmTask.id, status: nextStatus[confirmTask.status] });
      setConfirmTask(null);
    }
  };

  if (isLoading) {
    return <div className="p-8 text-center text-muted-foreground">Loading tasks...</div>;
  }

  const tasks = myTasks || [];
  const now = new Date();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">My Tasks</h1>
        <p className="text-muted-foreground text-sm mt-1">{tasks.length} tasks assigned to you</p>
      </div>

      <div className="rounded-lg border bg-card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Title</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Severity</TableHead>
              <TableHead className="hidden sm:table-cell">Due Date</TableHead>
              <TableHead className="hidden md:table-cell">Transaction</TableHead>
              <TableHead className="text-right">Action</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {tasks.map((task: Task) => {
              const overdue = task.status === "overdue" || (task.status !== "done" && task.due_at && new Date(task.due_at) < now);
              return (
                <TableRow key={task.id}>
                  <TableCell>
                    <span className="font-medium text-foreground">{task.title}</span>
                    {overdue && task.status !== "overdue" && (
                      <Badge className="ml-2 bg-destructive/15 text-destructive text-xs">Overdue</Badge>
                    )}
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline" className={statusStyle[task.status] || statusStyle.todo}>
                      {task.status.replace("_", " ")}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline" className={severityStyle[task.severity] || severityStyle.medium}>
                      {task.severity}
                    </Badge>
                  </TableCell>
                  <TableCell className="hidden sm:table-cell text-muted-foreground text-sm">
                    {task.due_at ? new Date(task.due_at).toLocaleDateString() : "—"}
                  </TableCell>
                  <TableCell className="hidden md:table-cell text-muted-foreground text-sm">
                    {task.transaction_title}
                  </TableCell>
                  <TableCell className="text-right">
                    {task.status === "done" ? (
                      <span className="text-xs text-muted-foreground mr-4 flex items-center justify-end gap-1">
                        <CheckCircle2 className="w-3 h-3 text-success" /> Completed
                      </span>
                    ) : (
                      <Button
                        variant={task.status === "todo" || task.status === "overdue" ? "secondary" : "outline"}
                        size="sm"
                        onClick={() => setConfirmTask(task)}
                        className="text-xs"
                      >
                        {task.status === "todo" || task.status === "overdue" ? "Start Task" : "Mark Done"}
                      </Button>
                    )}
                  </TableCell>
                </TableRow>
              );
            })}
            {tasks.length === 0 && (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                  You have no assigned tasks.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      <AlertDialog open={!!confirmTask} onOpenChange={(isOpen) => !isOpen && !mutation.isPending && setConfirmTask(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Update Task Status</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to mark this task as <span className="font-semibold text-foreground">{confirmTask ? nextStatus[confirmTask.status]?.replace("_", " ") : ""}</span>?
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={mutation.isPending}>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={(e) => { e.preventDefault(); confirmToggleStatus(); }} disabled={mutation.isPending}>
              {mutation.isPending ? "Updating..." : "Update Status"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default TasksPage;
