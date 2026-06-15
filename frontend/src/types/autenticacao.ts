export type PapelUsuario = "admin" | "entrepreneur" | "collaborator";


export type CapacidadesUsuario = {
  gerenciar_usuarios: boolean;
  dados_mestres: boolean;
  estoque_leitura: boolean;
  estoque_movimentacoes: boolean;
  receitas_producao: boolean;
  financeiro: boolean;
  relatorios: boolean;
  painel: boolean;
};


export type UsuarioSessao = {
  id: number;
  username: string;
  email: string;
  papel: PapelUsuario;
  senha_temporaria: boolean;
  capacidades: CapacidadesUsuario;
};


export const ROTULOS_PAPEL: Record<PapelUsuario, string> = {
  admin: "Administrador",
  entrepreneur: "Empreendedor",
  collaborator: "Colaborador",
};

