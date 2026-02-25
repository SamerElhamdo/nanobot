import { Routes, Route, Navigate } from "react-router-dom";
import { Login } from "./pages/Login";
import { Layout } from "./components/Layout";
import { ConfigPage } from "./pages/ConfigPage";
import { WorkspacePage } from "./pages/WorkspacePage";
import { SkillsPage } from "./pages/SkillsPage";
import { EnvPage } from "./pages/EnvPage";

function RequireAuth({ children }: { children: React.ReactNode }) {
  const token = sessionStorage.getItem("nanobot_admin_token");
  if (!token) return <Navigate to="/" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Login />} />
      <Route
        path="/admin"
        element={
          <RequireAuth>
            <Layout />
          </RequireAuth>
        }
      >
        <Route index element={<Navigate to="config" replace />} />
        <Route path="config" element={<ConfigPage />} />
        <Route path="workspace" element={<WorkspacePage />} />
        <Route path="skills" element={<SkillsPage />} />
        <Route path="env" element={<EnvPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
