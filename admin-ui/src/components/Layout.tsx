import { Outlet, NavLink, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const nav = [
  { to: "config", label: "Config" },
  { to: "workspace", label: "Workspace" },
  { to: "skills", label: "Skills" },
  { to: "env", label: "Env vars" },
];

export function Layout() {
  const navigate = useNavigate();

  function handleLogout() {
    sessionStorage.removeItem("nanobot_admin_token");
    navigate("/", { replace: true });
  }

  return (
    <div className="flex h-screen bg-background">
      <aside className="w-56 border-r flex flex-col">
        <div className="p-4 border-b font-semibold">Nanobot Admin</div>
        <nav className="flex-1 p-2 space-y-1">
          {nav.map(({ to, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                cn(
                  "block px-3 py-2 rounded-md text-sm",
                  isActive ? "bg-primary text-primary-foreground" : "hover:bg-accent"
                )
              }
            >
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="p-2">
          <Button variant="outline" size="sm" className="w-full" onClick={handleLogout}>
            Sign out
          </Button>
        </div>
      </aside>
      <main className="flex-1 overflow-auto p-6">
        <Outlet />
      </main>
    </div>
  );
}
