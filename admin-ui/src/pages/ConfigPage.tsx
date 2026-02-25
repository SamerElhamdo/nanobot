import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { configApi } from "@/api/client";

export function ConfigPage() {
  const [config, setConfig] = useState<string>("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    configApi.get().then((c) => setConfig(JSON.stringify(c, null, 2))).catch(setError);
  }, []);

  function handleSave() {
    setError("");
    setSaving(true);
    try {
      const parsed = JSON.parse(config) as Record<string, unknown>;
      configApi.patch(parsed).then(() => setError("Saved.")).catch(setError);
    } catch {
      setError("Invalid JSON");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Config</CardTitle>
          <p className="text-sm text-muted-foreground">Edit ~/.nanobot/config.json</p>
        </CardHeader>
        <CardContent className="space-y-4">
          {error && (
            <p className={error === "Saved." ? "text-sm text-green-600" : "text-sm text-destructive"}>
              {error}
            </p>
          )}
          <textarea
            className="w-full h-[60vh] font-mono text-sm rounded-md border border-input bg-background p-3"
            value={config}
            onChange={(e) => setConfig(e.target.value)}
            spellCheck={false}
          />
          <Button onClick={handleSave} disabled={saving}>
            {saving ? "Saving…" : "Save"}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
