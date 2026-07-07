// Phase 1 shim: until Supabase Auth lands (Phase 2), the app renders as the
// user named by VIEW_AS_EMAIL. Replaced by lib/auth.ts getUser() in Phase 2.
import "server-only";
import { getUserByEmail } from "./db";
import type { AppUser } from "./rounds";

export async function getViewer(): Promise<AppUser | null> {
  const email = process.env.VIEW_AS_EMAIL;
  if (!email) return null;
  return getUserByEmail(email);
}
