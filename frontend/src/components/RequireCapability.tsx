import { Navigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import type { UserCapabilities } from "../types/auth";

type CapKey = keyof UserCapabilities;

export function RequireCapability({
  need,
  children,
}: {
  need: CapKey;
  children: React.ReactNode;
}) {
  const { user } = useAuth();
  if (!user?.capabilities?.[need]) {
    return <Navigate to="/app" replace />;
  }
  return <>{children}</>;
}
