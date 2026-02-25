import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { skillsApi } from "@/api/client";

export function SkillsPage() {
  const [skills, setSkills] = useState<{ name: string; path: string; source: string }[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [content, setContent] = useState("");
  const [source, setSource] = useState<"workspace" | "builtin">("workspace");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    skillsApi.list().then(setSkills).catch(setError);
  }, []);

  useEffect(() => {
    if (!selected) {
      setContent("");
      return;
    }
    skillsApi
      .get(selected)
      .then((r) => {
        setContent(r.content);
        setSource(r.source as "workspace" | "builtin");
      })
      .catch(() => setContent(""));
  }, [selected]);

  function handleSave() {
    if (!selected || source !== "workspace") return;
    setError("");
    setSaving(true);
    skillsApi
      .put(selected, content)
      .then(() => setError("Saved."))
      .catch(setError)
      .finally(() => setSaving(false));
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Skills</CardTitle>
          <p className="text-sm text-muted-foreground">Workspace and built-in skills (SKILL.md)</p>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2 flex-wrap">
            {skills.map((s) => (
              <Button
                key={s.name}
                variant={selected === s.name ? "default" : "outline"}
                size="sm"
                onClick={() => setSelected(s.name)}
              >
                {s.name}
                <span className="ml-1 text-muted-foreground">({s.source})</span>
              </Button>
            ))}
          </div>
          {selected && (
            <>
              {source === "builtin" && (
                <p className="text-sm text-muted-foreground">Read-only (built-in skill).</p>
              )}
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
                readOnly={source === "builtin"}
                spellCheck={false}
              />
              {source === "workspace" && (
                <Button onClick={handleSave} disabled={saving}>
                  {saving ? "Saving…" : "Save"}
                </Button>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
