import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { MOCK_TRANSACTIONS, MOCK_TIMELINE, MOCK_HEALTH, MOCK_TASKS, MOCK_USERS } from "@/lib/mock-data";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowLeft, CheckCircle2, Clock, AlertTriangle, Circle, UserPlus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { useToast } from "@/hooks/use-toast";
import CreateTaskDialog from "@/components/CreateTaskDialog";
import type { HealthStatus, Task, TaskStatus, TimelineItem } from "@/lib/types";

const healthColor: Record<HealthStatus, { bg: string; icon: typeof CheckCircle2 }> = {
  GREEN: { bg: "bg-success text-success-foreground", icon: CheckCircle2 },
  YELLOW: { bg: "bg-warning text-warning-foreground", icon: Clock },
  RED: { bg: "bg-destructive text-destructive-foreground", icon: AlertTriangle },
};

const severityBadge: Record<string, string> = {
  critical: "bg-destructive/15 text-destructive",
  high: "bg-warning/15 text-warning",
  medium: "bg-muted text-muted-foreground",
  low: "bg-accent text-accent-foreground",
};

const TASK_STATUSES: TaskStatus[] = ["todo", "in_progress", "done"];

const TransactionDetailPage = () => {
  const { id } = useParams<{ id: string }>();
  const tx = MOCK_TRANSACTIONS.find((t) => t.id === id);
  const health = MOCK_HEALTH[id || ""];
  const { toast } = useToast();

  const [timelineItems, setTimelineItems] = useState<TimelineItem[]>(
    () => MOCK_TIMELINE[id || ""] || []
  );
  const [tasks, setTasks] = useState<Task[]>(
    () => MOCK_TASKS.filter((t) => t.transaction_id === id)
  );

  if (!tx) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">Transaction not found.</p>
        <Link to="/dashboard/transactions">
          <Button variant="outline" className="mt-4">Back to Transactions</Button>
        </Link>
      </div>
    );
  }

  const now = new Date();

  const handleMarkComplete = (itemId: string) => {
    setTimelineItems((prev) =>
      prev.map((item) =>
        item.id === itemId
          ? { ...item, completed_at: new Date().toISOString(), updated_at: new Date().toISOString() }
          : item
      )
    );
    toast({ title: "Timeline updated", description: "Item marked as complete." });
  };

  const handleTaskStatusChange = (taskId: string, newStatus: TaskStatus) => {
    setTasks((prev) =>
      prev.map((t) =>
        t.id === taskId ? { ...t, status: newStatus, updated_at: new Date().toISOString() } : t
      )
    );
    toast({ title: "Task updated", description: `Status changed to ${newStatus.replace("_", " ")}.` });
  };

  const handleAssignTask = (taskId: string, userId: string) => {
    setTasks((prev) =>
      prev.map((t) =>
        t.id === taskId ? { ...t, assignee_id: userId, updated_at: new Date().toISOString() } : t
      )
    );
    const user = MOCK_USERS.find((u) => u.id === userId);
    toast({ title: "Task assigned", description: `Assigned to ${user?.full_name || userId}.` });
  };

  const handleTaskCreated = (task: Task) => {
    setTasks((prev) => [...prev, task]);
  };

  const getAssigneeName = (assigneeId?: string) => {
    if (!assigneeId) return "Unassigned";
    return MOCK_USERS.find((u) => u.id === assigneeId)?.full_name || assigneeId;
  };

  return (
    <div className="space-y-6 max-w-4xl">
      <Link to="/dashboard/transactions" className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground">
        <ArrowLeft className="h-4 w-4 mr-1" /> Back to Transactions
      </Link>

      {/* Deal Info */}
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-foreground">{tx.title}</h1>
          <p className="text-muted-foreground text-sm mt-1">{tx.property_address}</p>
          {tx.description && (
            <p className="text-muted-foreground text-sm mt-1">{tx.description}</p>
          )}
        </div>
        <div className="flex items-center gap-2">
          {health && (
            <Badge className={healthColor[health.status].bg}>{health.status}</Badge>
          )}
          <Badge variant="outline">{tx.status}</Badge>
        </div>
      </div>

      {/* Health Reasons */}
      {health && health.reasons.length > 0 && (
        <Card className={health.status === "RED" ? "border-destructive/30" : "border-warning/30"}>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              <AlertTriangle className={`h-4 w-4 ${health.status === "RED" ? "text-destructive" : "text-warning"}`} />
              Health Issues
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-1">
              {health.reasons.map((r, i) => (
                <li key={i} className="text-sm text-muted-foreground flex items-center gap-2">
                  <span className={`h-1.5 w-1.5 rounded-full ${health.status === "RED" ? "bg-destructive" : "bg-warning"}`} />
                  {r}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Deal Details Grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {[
          { label: "Close Date", value: tx.close_date || "—" },
          { label: "Org ID", value: tx.org_id },
          { label: "Created", value: new Date(tx.created_at).toLocaleDateString() },
        ].map((item) => (
          <Card key={item.label}>
            <CardContent className="pt-4">
              <p className="text-xs text-muted-foreground">{item.label}</p>
              <p className="text-lg font-semibold text-foreground mt-1">{item.value}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Timeline */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Timeline</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="relative space-y-0">
            {timelineItems.map((item, i) => {
              const due = item.due_at ? new Date(item.due_at) : null;
              const completed = !!item.completed_at;
              const overdue = !completed && due && due < now;
              const dueSoon = !completed && !overdue && due && (due.getTime() - now.getTime()) < 3 * 86400000;

              return (
                <div key={item.id} className="flex gap-4 pb-6 last:pb-0">
                  <div className="flex flex-col items-center">
                    {completed ? (
                      <CheckCircle2 className="h-5 w-5 text-success shrink-0" />
                    ) : overdue ? (
                      <AlertTriangle className="h-5 w-5 text-destructive shrink-0" />
                    ) : dueSoon ? (
                      <Clock className="h-5 w-5 text-warning shrink-0" />
                    ) : (
                      <Circle className="h-5 w-5 text-muted-foreground shrink-0" />
                    )}
                    {i < timelineItems.length - 1 && (
                      <div className="w-px flex-1 bg-border mt-1" />
                    )}
                  </div>
                  <div className="pb-2 flex-1">
                    <p className="font-medium text-foreground text-sm">{item.label}</p>
                    {item.description && (
                      <p className="text-xs text-muted-foreground">{item.description}</p>
                    )}
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xs text-muted-foreground">
                        Due: {due ? due.toLocaleDateString() : "—"}
                      </span>
                      {completed && <Badge className="bg-success/15 text-success text-xs">Completed</Badge>}
                      {overdue && <Badge className="bg-destructive/15 text-destructive text-xs">Overdue</Badge>}
                      {dueSoon && <Badge className="bg-warning/15 text-warning text-xs">Due Soon</Badge>}
                      {!completed && (
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-6 px-2 text-xs text-muted-foreground hover:text-success"
                          onClick={() => handleMarkComplete(item.id)}
                        >
                          <CheckCircle2 className="h-3 w-3 mr-1" /> Mark Complete
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Tasks */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-lg">Tasks ({tasks.length})</CardTitle>
          <CreateTaskDialog
            transactionId={tx.id}
            transactionTitle={tx.title}
            onTaskCreated={handleTaskCreated}
          />
        </CardHeader>
        <CardContent>
          {tasks.length === 0 ? (
            <p className="text-sm text-muted-foreground">No tasks for this transaction.</p>
          ) : (
            <div className="space-y-2">
              {tasks.map((task) => {
                const taskStatusClass =
                  task.status === "done" ? "bg-success/15 text-success" :
                  task.status === "in_progress" ? "bg-warning/15 text-warning" :
                  task.status === "overdue" ? "bg-destructive/15 text-destructive" :
                  "bg-muted text-muted-foreground";
                return (
                  <div key={task.id} className="rounded-lg border p-3 space-y-2">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium text-sm text-foreground">{task.title}</p>
                        {task.description && (
                          <p className="text-xs text-muted-foreground">{task.description}</p>
                        )}
                        <p className="text-xs text-muted-foreground mt-0.5">
                          Due: {task.due_at ? new Date(task.due_at).toLocaleDateString() : "—"}
                          {" · "}{getAssigneeName(task.assignee_id)}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className={severityBadge[task.severity]}>{task.severity}</Badge>
                        <Badge variant="outline" className={taskStatusClass}>{task.status.replace("_", " ")}</Badge>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Select
                        value={task.status}
                        onValueChange={(v) => handleTaskStatusChange(task.id, v as TaskStatus)}
                      >
                        <SelectTrigger className="h-7 w-[130px] text-xs">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {TASK_STATUSES.map((s) => (
                            <SelectItem key={s} value={s}>{s.replace("_", " ")}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <Popover>
                        <PopoverTrigger asChild>
                          <Button variant="ghost" size="sm" className="h-7 px-2 text-xs">
                            <UserPlus className="h-3 w-3 mr-1" /> Assign
                          </Button>
                        </PopoverTrigger>
                        <PopoverContent className="w-48 p-2">
                          <div className="space-y-1">
                            {MOCK_USERS.map((u) => (
                              <Button
                                key={u.id}
                                variant={task.assignee_id === u.id ? "secondary" : "ghost"}
                                size="sm"
                                className="w-full justify-start text-xs h-7"
                                onClick={() => handleAssignTask(task.id, u.id)}
                              >
                                {u.full_name}
                              </Button>
                            ))}
                          </div>
                        </PopoverContent>
                      </Popover>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default TransactionDetailPage;
