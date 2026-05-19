export type UserRole = "admin" | "entrepreneur" | "collaborator";

export type UserCapabilities = {
  manage_users: boolean;
  master_data: boolean;
  stock_read: boolean;
  stock_movements: boolean;
  recipes_production: boolean;
  finance: boolean;
  reports: boolean;
  dashboard: boolean;
};

export type MeUser = {
  id: number;
  username: string;
  email: string;
  role: UserRole;
  capabilities: UserCapabilities;
};

export const ROLE_LABELS: Record<UserRole, string> = {
  admin: "Administrador",
  entrepreneur: "Empreendedor",
  collaborator: "Colaborador",
};
