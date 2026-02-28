import { getAuthMe } from "@/lib/api";
import { AuthMeResponse } from "@/lib/types";

export async function fetchSession(): Promise<AuthMeResponse | null> {
  try {
    return await getAuthMe();
  } catch {
    return null;
  }
}
