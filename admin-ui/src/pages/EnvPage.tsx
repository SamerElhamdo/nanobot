import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { envApi } from "@/api/client";

export function EnvPage() {
  const [vars, setVars] = useState<{ key: string; set: boolean; masked: string }[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    envApi.list().then(setVars).catch(setError);
  }, []);

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Environment variables</CardTitle>
          <p className="text-sm text-muted-foreground">Read-only. Set in environment or .env.</p>
        </CardHeader>
        <CardContent>
          {error && <p className="text-sm text-destructive">{error}</p>}
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="border-b">
                <th className="text-left py-2 pr-4">Key</th>
                <th className="text-left py-2 pr-4">Set</th>
                <th className="text-left py-2">Value</th>
              </tr>
            </thead>
            <tbody>
              {vars.map((v) => (
                <tr key={v.key} className="border-b">
                  <td className="py-2 pr-4 font-mono">{v.key}</td>
                  <td className="py-2 pr-4">{v.set ? "Yes" : "No"}</td>
                  <td className="py-2 font-mono text-muted-foreground">{v.masked || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}
