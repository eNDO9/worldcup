// Phase 3 shim: until real auth lands, the app renders as the user named by
// VIEW_AS_EMAIL. Replaced by lib/auth.ts getUser() when Supabase Auth ships.
import "server-only";
import { getAdminClient } from "./supabase/admin";
import { ensureEntry, getSettings } from "./nflDb";
import type { Entry } from "./nfl";

export interface Viewer {
  id: string;
  email: string;
  entry: Entry;
}

export async function getViewer(): Promise<Viewer | null> {
  const email = process.env.VIEW_AS_EMAIL;
  if (!email) return null;

  const { data, error } = await getAdminClient()
    .from("app_users").select("id, email").eq("email", email.toLowerCase().trim()).limit(1);
  if (error || !data?.[0]) return null;

  const user = data[0] as { id: string; email: string };
  const { season } = await getSettings();
  return { ...user, entry: await ensureEntry(user.id, season) };
}
