import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { HealthStatus } from "@/lib/types";
import { getTransactions } from "@/lib/api";
import { Skeleton } from "@/components/ui/skeleton";
import CreateTransactionDialog from "@/components/CreateTransactionDialog";

const statusVariant = (s: string) => {
  const map: Record<string, string> = {
    active: "bg-success/15 text-success border-success/30",
    pending: "bg-warning/15 text-warning border-warning/30",
    draft: "bg-muted text-muted-foreground",
    closed: "bg-primary/10 text-primary",
    cancelled: "bg-destructive/15 text-destructive",
  };
  return map[s] || "bg-muted text-muted-foreground";
};

const healthBadge = (status: HealthStatus) => {
  const map: Record<HealthStatus, string> = {
    GREEN: "bg-success text-success-foreground",
    YELLOW: "bg-warning text-warning-foreground",
    RED: "bg-destructive text-destructive-foreground",
  };
  return map[status] || map.GREEN;
};

const TransactionsPage = () => {
  const { data: transactions, isLoading, refetch } = useQuery({ queryKey: ["transactions"], queryFn: getTransactions });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <Skeleton className="h-8 w-48" />
            <Skeleton className="h-4 w-32 mt-2" />
          </div>
          <Skeleton className="h-10 w-40" />
        </div>
        <div className="rounded-lg border bg-card">
          <Table>
            <TableHeader>
              <TableRow>
                {["Title", "Status", "Health", "Address", "Close Date", "Created"].map((h) => (
                  <TableHead key={h}><Skeleton className="h-4 w-16" /></TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {[...Array(5)].map((_, i) => (
                <TableRow key={i}>
                  {[...Array(6)].map((_, j) => (
                    <TableCell key={j}><Skeleton className="h-4 w-full" /></TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </div>
    );
  }

  const txList = transactions || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Transactions</h1>
          <p className="text-muted-foreground text-sm mt-1">{txList.length} total transactions</p>
        </div>
        <CreateTransactionDialog onCreated={() => refetch()} />
      </div>

      <div className="rounded-lg border bg-card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Title</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Health</TableHead>
              <TableHead className="hidden md:table-cell">Property Address</TableHead>
              <TableHead className="hidden sm:table-cell">Close Date</TableHead>
              <TableHead className="hidden lg:table-cell">Created</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {txList.map((tx) => {
              const health = tx.health_score || "GREEN";
              return (
                <TableRow key={tx.id} className="cursor-pointer hover:bg-accent/50">
                  <TableCell>
                    <Link to={`/dashboard/transactions/${tx.id}`} className="font-medium text-foreground hover:text-primary">
                      {tx.title}
                    </Link>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline" className={statusVariant(tx.status)}>
                      {tx.status}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge className={healthBadge(health)} variant="secondary">
                      {health}
                    </Badge>
                  </TableCell>
                  <TableCell className="hidden md:table-cell text-muted-foreground text-sm">
                    {tx.property_address}
                  </TableCell>
                  <TableCell className="hidden sm:table-cell text-muted-foreground text-sm">
                    {tx.close_date}
                  </TableCell>
                  <TableCell className="hidden lg:table-cell text-muted-foreground text-sm">
                    {new Date(tx.created_at).toLocaleDateString()}
                  </TableCell>
                </TableRow>
              );
            })}
            {txList.length === 0 && (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                  No transactions found. Create one to get started.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
};

export default TransactionsPage;
