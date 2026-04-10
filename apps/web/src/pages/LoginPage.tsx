import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { authLogin } from "@/lib/api";
import { login as authStoreLogin } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Building2 } from "lucide-react";

const LoginPage = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState("admin@dev.local");
  const [password, setPassword] = useState("password123");
  const [error, setError] = useState("");

  const loginMutation = useMutation({
    mutationFn: () => authLogin(email, password),
    onSuccess: (data) => {
      authStoreLogin(data.access_token, {
        id: "sys_user",
        email,
        full_name: email.split("@")[0],
        is_active: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      });
      navigate("/dashboard");
    },
    onError: (err: any) => {
      setError(err.message || "Login failed. Please try again.");
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (email && password.length >= 4) {
      loginMutation.mutate();
    } else {
      setError("Please enter a valid email and password (min 4 chars).");
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <Card className="w-full max-w-md shadow-lg">
        <CardHeader className="text-center space-y-2">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-primary">
            <Building2 className="h-6 w-6 text-primary-foreground" />
          </div>
          <CardTitle className="text-2xl font-bold">Welcome back</CardTitle>
          <CardDescription>Sign in to your transaction dashboard</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="rounded-lg bg-destructive/10 p-3 text-sm text-destructive">
                {error}
              </div>
            )}
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="admin@dev.local"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                disabled={loginMutation.isPending}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={loginMutation.isPending}
              />
            </div>
            <Button type="submit" className="w-full" disabled={loginMutation.isPending}>
              {loginMutation.isPending ? "Signing in…" : "Sign in"}
            </Button>
            <p className="text-xs text-muted-foreground text-center">
              Dev credentials: admin@dev.local / password123
            </p>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

export default LoginPage;
