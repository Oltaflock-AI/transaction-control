import { useState } from "react";
import { Link } from "react-router-dom";
import { MOCK_TRANSACTIONS, MOCK_HEALTH } from "@/lib/mock-data";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { HealthStatus, Transaction } from "@/lib/types";
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
  return map[status];
};

const TransactionsPage = () => {
  const [transactions, setTransactions] = useState<Transaction[]>(MOCK_TRANSACTIONS);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Transactions</h1>
          <p className="text-muted-foreground text-sm mt-1">{transactions.length} total transactions</p>
        </div>
        <CreateTransactionDialog onCreated={(tx) => setTransactions((prev) => [...prev, tx])} />
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
            {transactions.map((tx) => {
              const health = MOCK_HEALTH[tx.id];
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
                    {health && (
                      <Badge className={healthBadge(health.status)} variant="secondary">
                        {health.status}
                      </Badge>
                    )}
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
          </TableBody>
        </Table>
      </div>
    </div>
  );
};

export default TransactionsPage;
