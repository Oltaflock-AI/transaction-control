import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getTransaction, getTransactionTimeline, getTransactionHealth, markTimelineItemComplete, updateTaskStatus, assignTask, getTransactionMembers } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowLeft, CheckCircle2, Clock, AlertTriangle, Circle, UserPlus } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
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
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const { data: tx, isLoading: txLoading } = useQuery({
    queryKey: ["transaction", id],
    queryFn: () => getTransaction(id!),
    enabled: !!id,
  });

  const { data: health, isLoading: healthLoading } = useQuery({
    queryKey: ["health", id],
    queryFn: () => getTransactionHealth(id!),
    enabled: !!id,
  });

  const { data: timelineItemsData, isLoading: timelineLoading } = useQuery({
    queryKey: ["timeline", id],
    queryFn: () => getTransactionTimeline(id!),
    enabled: !!id,
  });

  const { data: users } = useQuery({
    queryKey: ["transactionMembers", id],
    queryFn: () => getTransactionMembers(id!),
    enabled: !!id,
  });

  const completeTimelineMutation = useMutation({
    mutationFn: (itemId: string) => markTimelineItemComplete(itemId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["timeline", id] });
      toast({ title: "Timeline updated", description: "Item marked as complete." });
    },
    onError: (err: any) => toast({ title: "Update failed", description: err.message, variant: "destructive" }),
  });

  const updateStatusMutation = useMutation({
    mutationFn: ({ taskId, status }: { taskId: string, status: string }) => updateTaskStatus(taskId, status),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["transaction", id] });
      toast({ title: "Task updated", description: `Status changed to ${variables.status.replace("_", " ")}.` });
    },
    onError: (err: any) => toast({ title: "Update failed", description: err.message, variant: "destructive" }),
  });

  const assignTaskMutation = useMutation({
    mutationFn: ({ taskId, userId }: { taskId: string, userId: string }) => assignTask(taskId, userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["transaction", id] });
      toast({ title: "Task assigned" });
    },
    onError: (err: any) => toast({ title: "Assignment failed", description: err.message, variant: "destructive" }),
  });

  if (txLoading || healthLoading || timelineLoading) {
    return (
      <div className="space-y-6 max-w-4xl">
        <Skeleton className="h-4 w-40" />
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
          <div>
            <Skeleton className="h-8 w-64" />
            <Skeleton className="h-4 w-48 mt-2" />
          </div>
          <div className="flex gap-2">
            <Skeleton className="h-6 w-16 rounded-full" />
            <Skeleton className="h-6 w-16 rounded-full" />
          </div>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[...Array(3)].map((_, i) => (
            <Card key={i}><CardContent className="pt-4"><Skeleton className="h-4 w-20" /><Skeleton className="h-6 w-32 mt-2" /></CardContent></Card>
          ))}
        </div>
        <Card>
          <CardHeader><Skeleton className="h-5 w-24" /></CardHeader>
          <CardContent className="space-y-4">
            {[...Array(4)].map((_, i) => <Skeleton key={i} className="h-16 w-full" />)}
          </CardContent>
        </Card>
        <Card>
          <CardHeader><Skeleton className="h-5 w-32" /></CardHeader>
          <CardContent className="space-y-4">
            {[...Array(3)].map((_, i) => <Skeleton key={i} className="h-16 w-full" />)}
          </CardContent>
        </Card>
      </div>
    );
  }

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
  const timelineItems = timelineItemsData || [];
  const tasks = tx.tasks || [];

  const handleMarkComplete = (itemId: string) => completeTimelineMutation.mutate(itemId);
  const handleTaskStatusChange = (taskId: string, newStatus: TaskStatus) => updateStatusMutation.mutate({ taskId, status: newStatus });
  const handleAssignTask = (taskId: string, userId: string) => assignTaskMutation.mutate({ taskId, userId });
  const handleTaskCreated = (task: Task) => queryClient.invalidateQueries({ queryKey: ["transaction", id] });

  const getAssigneeName = (assigneeId?: string) => {
    if (!assigneeId) return "Unassigned";
    const member = (users || []).find((u) => u.id === assigneeId);
    return member?.full_name || assigneeId;
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
            <Badge className={healthColor[health.score]?.bg || healthColor.GREEN.bg}>{health.score}</Badge>
          )}
          <Badge variant="outline">{tx.status}</Badge>
        </div>
      </div>

      {/* Health Reasons */}
      {health && health.reasons.length > 0 && (
        <Card className={health.score === "RED" ? "border-destructive/30" : "border-warning/30"}>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              <AlertTriangle className={`h-4 w-4 ${health.score === "RED" ? "text-destructive" : "text-warning"}`} />
              Health Issues
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-1">
              {health.reasons.map((r: string, i: number) => (
                <li key={i} className="text-sm text-muted-foreground flex items-center gap-2">
                  <span className={`h-1.5 w-1.5 rounded-full ${health.score === "RED" ? "bg-destructive" : "bg-warning"}`} />
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
            {timelineItems.length === 0 && (
              <p className="text-sm text-muted-foreground">No timeline items generated yet.</p>
            )}
            {timelineItems.map((item: TimelineItem, i: number) => {
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
                          disabled={completeTimelineMutation.isPending}
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
            <div className="relative space-y-0">
              {tasks.map((task: Task, i: number) => {
                const due = task.due_at ? new Date(task.due_at) : null;
                const completed = task.status === "done";
                const todo = task.status === "todo";
                const overdue = !completed && due && due < now;
                const dueSoon = !completed && !overdue && due && (due.getTime() - now.getTime()) < 3 * 86400000;

                return (
                  <div key={task.id} className="flex gap-4 pb-6 last:pb-0">
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
                      {i < tasks.length - 1 && (
                        <div className="w-px flex-1 bg-border mt-1" />
                      )}
                    </div>
                    <div className="pb-2 flex-1">
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <p className="font-medium text-foreground text-sm">{task.title} <Badge variant="outline" className='bg-muted text-muted-foreground'>{task.severity}</Badge></p>
                          {task.description && (
                            <p className="text-xs text-muted-foreground">{task.description}</p>
                          )}
                          <div className="flex items-center flex-wrap gap-2 mt-1">
                            <span className="text-xs text-muted-foreground">
                              Due: {due ? due.toLocaleDateString() : "—"}
                              {" · "}{getAssigneeName(task.assignee_id)}
                            </span>
                            {todo && <Badge className="bg-warning/15 text-warning text-xs">Todo</Badge>}
                            {completed && <Badge className="bg-success/15 text-success text-xs">Completed</Badge>}
                            {overdue && <Badge className="bg-destructive/15 text-destructive text-xs">Overdue</Badge>}
                            {dueSoon && <Badge className="bg-warning/15 text-warning text-xs">Due Soon</Badge>}
                          </div>
                        </div>
                        <div className="flex items-center gap-2 shrink-0">
                          <Popover>
                            <PopoverTrigger asChild>
                              <Button variant="ghost" size="sm" className="h-7 px-2 text-xs" disabled={assignTaskMutation.isPending}>
                                <UserPlus className="h-3 w-3 mr-1" /> Assign
                              </Button>
                            </PopoverTrigger>
                            <PopoverContent className="w-48 p-2">
                              <div className="space-y-1">
                                {users && users.length > 0 ? users.map((u) => (
                                  <Button
                                    key={u.id}
                                    variant={task.assignee_id === u.id ? "secondary" : "ghost"}
                                    size="sm"
                                    className="w-full justify-start text-xs h-7"
                                    onClick={() => handleAssignTask(task.id, u.id)}
                                  >
                                    {u.full_name}
                                  </Button>
                                )) : <div className="text-xs p-2 text-muted-foreground">No users found</div>}
                              </div>
                            </PopoverContent>
                          </Popover>
                        </div>
                      </div>
                      {!completed && (
                        <div className="mt-2 flex items-center gap-2">
                          <Button
                            size="sm"
                            variant="ghost"
                            className="h-6 px-2 text-xs text-muted-foreground hover:text-success"
                            onClick={() => handleTaskStatusChange(task.id, "done")}
                            disabled={updateStatusMutation.isPending}
                          >
                            <CheckCircle2 className="h-3 w-3 mr-1" /> Mark Complete
                          </Button>
                        </div>
                      )}
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
