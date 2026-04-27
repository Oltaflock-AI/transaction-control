import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getAuditEvents, getTransactions } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Shield, ArrowRightLeft, CheckSquare, Clock, User } from "lucide-react";
import type { AuditEvent } from "@/lib/types";

const entityIcons: Record<string, typeof Shield> = {
  transaction: ArrowRightLeft,
  task: CheckSquare,
  timeline: Clock,
  user: User,
};

const actionColor: Record<string, string> = {
  "transaction.created": "bg-success/15 text-success",
  "task.created": "bg-success/15 text-success",
  "task.status_updated": "bg-primary/15 text-primary",
  "timeline.completed": "bg-success/15 text-success",
  "task.marked_overdue": "bg-destructive/15 text-destructive",
  "transaction.closed": "bg-primary/15 text-primary",
};

const AuditPage = () => {
  const [filter, setFilter] = useState<string>("all");

  const { data: transactions, isLoading: txLoading } = useQuery({
    queryKey: ["transactions"],
    queryFn: getTransactions,
  });

  const orgId = transactions?.[0]?.org_id;

  const { data: auditData, isLoading: auditLoading } = useQuery({
    queryKey: ["audit", orgId, filter],
    queryFn: () => getAuditEvents({ org_id: orgId!, entity_type: filter !== "all" ? filter : undefined }),
    enabled: !!orgId,
  });

  const isLoading = txLoading || (auditLoading && !!orgId);

  const events = auditData?.items || [];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
            <Shield className="h-6 w-6" />
            Audit Log
          </h1>
          <p className="text-muted-foreground text-sm mt-1">Track all system activity</p>
        </div>
        <Select value={filter} onValueChange={setFilter}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Filter by type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            <SelectItem value="transaction">Transactions</SelectItem>
            <SelectItem value="task">Tasks</SelectItem>
            <SelectItem value="timeline">Timeline</SelectItem>
            <SelectItem value="user">Users</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {isLoading && (
        <div className="p-8 text-center text-muted-foreground">Loading audit log...</div>
      )}

      {!isLoading && !orgId && (
        <div className="p-8 text-center text-muted-foreground">
          You must have at least one transaction to view the organization audit log.
        </div>
      )}

      {!isLoading && orgId && (
        <div className="space-y-3">
          {events.map((event: AuditEvent) => {
            const Icon = entityIcons[event.entity_type] || Shield;
            return (
              <Card key={event.id}>
                <CardContent className="flex items-start gap-4 py-4">
                  <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-accent shrink-0">
                    <Icon className="h-4 w-4 text-accent-foreground" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <Badge variant="outline" className={actionColor[event.action] || "bg-muted text-muted-foreground"}>
                        {event.action}
                      </Badge>
                      <Badge variant="outline">{event.entity_type}</Badge>
                    </div>
                    <p className="text-sm text-foreground mt-1">{event.detail}</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      by {event.actor_name || "System"} · {new Date(event.created_at).toLocaleString()}
                    </p>
                  </div>
                </CardContent>
              </Card>
            );
          })}
          {events.length === 0 && (
            <p className="text-sm text-muted-foreground text-center py-8">No audit events found.</p>
          )}
        </div>
      )}
    </div>
  );
};

export default AuditPage;
