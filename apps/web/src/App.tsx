import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes, Navigate } from "react-router-dom";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import LoginPage from "./pages/LoginPage";
import DashboardLayout from "./pages/DashboardLayout";
import DashboardHome from "./pages/DashboardHome";
import TransactionsPage from "./pages/TransactionsPage";
import TransactionDetailPage from "./pages/TransactionDetailPage";
import TasksPage from "./pages/TasksPage";
import AuditPage from "./pages/AuditPage";
import TeamPage from "./pages/TeamPage";
import NotFound from "./pages/NotFound";
import ErrorBoundary from "@/components/ErrorBoundary";
import { isAdmin } from "@/lib/auth";

const AdminRoute = ({ children }: { children: React.ReactNode }) => {
  return isAdmin() ? <>{children}</> : <Navigate to="/dashboard" replace />;
};

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <ErrorBoundary>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Navigate to="/login" replace />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/dashboard" element={<DashboardLayout />}>
              <Route index element={<ErrorBoundary><DashboardHome /></ErrorBoundary>} />
              <Route path="transactions" element={<AdminRoute><ErrorBoundary><TransactionsPage /></ErrorBoundary></AdminRoute>} />
              <Route path="transactions/:id" element={<AdminRoute><ErrorBoundary><TransactionDetailPage /></ErrorBoundary></AdminRoute>} />
              <Route path="tasks" element={<ErrorBoundary><TasksPage /></ErrorBoundary>} />
              <Route path="team" element={<AdminRoute><ErrorBoundary><TeamPage /></ErrorBoundary></AdminRoute>} />
              <Route path="audit" element={<AdminRoute><ErrorBoundary><AuditPage /></ErrorBoundary></AdminRoute>} />
            </Route>
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </ErrorBoundary>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
