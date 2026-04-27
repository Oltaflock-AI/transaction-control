import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { getDashboardStats, getMyTasks } from "@/lib/api";
import { ArrowRightLeft, AlertTriangle, Clock, CheckCircle2 } from "lucide-react";

const DashboardHome = () => {
  const { data: stats, isLoading: statsLoading } = useQuery({ queryKey: ["dashboardStats"], queryFn: getDashboardStats });
  const { data: myTasks, isLoading: tasksLoading } = useQuery({ queryKey: ["myTasks"], queryFn: getMyTasks });

  if (statsLoading || tasksLoading) {
    return <div className="p-8 text-center text-muted-foreground">Loading dashboard...</div>;
  }

  if (!stats) {
    return <div className="p-8 text-center text-destructive">Failed to load dashboard stats.</div>;
  }

  const tasks = myTasks || [];
  const overdueTasks = tasks.filter(
    (t) => t.status === "overdue" || (t.status !== "done" && t.due_at && new Date(t.due_at) < new Date())
  );
  const completedTasks = tasks.filter(t => t.status === "done").length;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Dashboard</h1>
        <p className="text-muted-foreground text-sm mt-1">Overview of your transactions and tasks</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Transactions</CardTitle>
            <ArrowRightLeft className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{stats.total_transactions}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Tasks Overdue</CardTitle>
            <AlertTriangle className="h-4 w-4 text-destructive" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-destructive">{stats.tasks_overdue}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Due Soon</CardTitle>
            <Clock className="h-4 w-4 text-warning" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{stats.tasks_due_soon}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Completed</CardTitle>
            <CheckCircle2 className="h-4 w-4 text-success" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{completedTasks}</div>
          </CardContent>
        </Card>
      </div>

      {stats.deals_at_risk.length > 0 && (
        <Card className="border-destructive/30">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-destructive" />
              Deals at Risk
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {stats.deals_at_risk.map((deal) => (
                <Link
                  key={deal.id}
                  to={`/dashboard/transactions/${deal.id}`}
                  className="flex items-center justify-between rounded-lg border p-3 hover:bg-accent transition-colors"
                >
                  <div>
                    <p className="font-medium text-foreground">{deal.title}</p>
                    <p className="text-sm text-muted-foreground">{deal.property_address}</p>
                  </div>
                  <Badge className="bg-destructive text-destructive-foreground">At Risk</Badge>
                </Link>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {overdueTasks.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Overdue Tasks</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {overdueTasks.map((task) => (
                <div key={task.id} className="flex items-center justify-between rounded-lg border p-3">
                  <div>
                    <p className="font-medium text-foreground">{task.title}</p>
                    <p className="text-sm text-muted-foreground">{task.transaction_title}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="bg-destructive/15 text-destructive text-xs">{task.severity}</Badge>
                    <span className="text-sm text-destructive font-medium">
                      Due {task.due_at ? new Date(task.due_at).toLocaleDateString() : "—"}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default DashboardHome;
