import type { UserRole } from "../types/auth";
import { apiGet, apiPatch } from "./client";

export type AdminUserRow = {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
  role: UserRole;
  collab_master_data: boolean;
  collab_stock_read: boolean;
  collab_stock_movements: boolean;
  collab_recipes_production: boolean;
  collab_finance: boolean;
  collab_reports: boolean;
  collab_dashboard: boolean;
};

export type AdminUserPatch = Partial<{
  email: string;
  is_active: boolean;
  role: UserRole;
  collab_master_data: boolean;
  collab_stock_read: boolean;
  collab_stock_movements: boolean;
  collab_recipes_production: boolean;
  collab_finance: boolean;
  collab_reports: boolean;
  collab_dashboard: boolean;
}>;

export function listAdminUsers(): Promise<AdminUserRow[]> {
  return apiGet<AdminUserRow[]>("/auth/users/");
}

export function patchAdminUser(
  id: number,
  body: AdminUserPatch,
): Promise<AdminUserRow> {
  return apiPatch<AdminUserRow>(`/auth/users/${id}/`, body);
}
