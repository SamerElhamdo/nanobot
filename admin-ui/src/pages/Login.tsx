import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { login, health } from "@/api/client";

export function Login() {
  const [token, setToken] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [adminConfigured, setAdminConfigured] = useState<boolean | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    health()
      .then((r) => setAdminConfigured(r.admin_configured))
      .catch(() => setAdminConfigured(false));
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(token.trim());
      sessionStorage.setItem("nanobot_admin_token", token.trim());
      navigate("/admin", { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-muted/30 p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Nanobot Admin</CardTitle>
          <p className="text-sm text-muted-foreground">
            Enter your Gateway Admin Token to sign in.
          </p>
          {adminConfigured === false && (
            <p className="text-sm text-destructive">
              Admin UI is disabled: set GATEWAY_ADMIN_TOKEN (or NANOBOT_ADMIN_TOKEN) in the
              environment.
            </p>
          )}
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="token">Gateway Token</Label>
              <Input
                id="token"
                type="password"
                placeholder="Token"
                value={token}
                onChange={(e) => setToken(e.target.value)}
                disabled={adminConfigured === false}
                autoFocus
              />
            </div>
            {error && <p className="text-sm text-destructive">{error}</p>}
            <Button type="submit" className="w-full" disabled={loading || adminConfigured === false}>
              {loading ? "Signing in…" : "Sign in"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
