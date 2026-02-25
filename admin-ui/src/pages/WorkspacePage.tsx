import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { workspaceApi } from "@/api/client";

export function WorkspacePage() {
  const [fileList, setFileList] = useState<{ name: string; exists: boolean }[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [content, setContent] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    workspaceApi.listFiles().then(setFileList).catch(setError);
  }, []);

  useEffect(() => {
    if (!selected) {
      setContent("");
      return;
    }
    workspaceApi
      .getFile(selected)
      .then((r) => setContent(r.content))
      .catch(() => setContent(""));
  }, [selected]);

  function handleSave() {
    if (!selected) return;
    setError("");
    setSaving(true);
    workspaceApi
      .putFile(selected, content)
      .then(() => setError("Saved."))
      .catch(setError)
      .finally(() => setSaving(false));
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Workspace files</CardTitle>
          <p className="text-sm text-muted-foreground">Bootstrap files in workspace root</p>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2 flex-wrap">
            {fileList.map((f) => (
              <Button
                key={f.name}
                variant={selected === f.name ? "default" : "outline"}
                size="sm"
                onClick={() => setSelected(f.name)}
              >
                {f.name}
                {!f.exists && <span className="ml-1 text-muted-foreground">(new)</span>}
              </Button>
            ))}
          </div>
          {selected && (
            <>
              {error && (
                <p
                  className={
                    error === "Saved." ? "text-sm text-green-600" : "text-sm text-destructive"
                  }
                >
                  {error}
                </p>
              )}
              <textarea
                className="w-full h-[50vh] font-mono text-sm rounded-md border border-input bg-background p-3"
                value={content}
                onChange={(e) => setContent(e.target.value)}
                spellCheck={false}
              />
              <Button onClick={handleSave} disabled={saving}>
                {saving ? "Saving…" : "Save"}
              </Button>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
