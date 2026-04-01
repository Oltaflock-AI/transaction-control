import { useState } from "react";
import { MOCK_TASKS } from "@/lib/mock-data";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { Task, TaskStatus } from "@/lib/types";

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
  const [tasks, setTasks] = useState<Task[]>([...MOCK_TASKS]);

  const toggleStatus = (id: string) => {
    setTasks((prev) =>
      prev.map((t) =>
        t.id === id ? { ...t, status: nextStatus[t.status] } : t
      )
    );
  };

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
            {tasks.map((task) => {
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
                    <Badge variant="outline" className={statusStyle[task.status]}>
                      {task.status.replace("_", " ")}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline" className={severityStyle[task.severity]}>
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
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => toggleStatus(task.id)}
                      className="text-xs"
                    >
                      → {nextStatus[task.status].replace("_", " ")}
                    </Button>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>
    </div>
  );
};

export default TasksPage;
