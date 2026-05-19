import type { MeUser } from "../types/auth";
import { apiGet } from "./client";

export function fetchMe(): Promise<MeUser> {
  return apiGet<MeUser>("/auth/me/");
}
