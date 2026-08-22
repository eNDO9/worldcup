"use server";

import { revalidatePath } from "next/cache";
import { getViewer } from "@/lib/viewer";
import { getWeek, savePick, type SavePickError } from "@/lib/nflDb";

/** Save the viewer's pick. Every rule is re-checked server-side in
 * savePick — the client's optimistic state is never trusted. */
export async function submitPick(
  weekId: number,
  teamAbbr: string,
): Promise<{ ok: true } | { ok: false; error: SavePickError }> {
  const viewer = await getViewer();
  if (!viewer) return { ok: false, error: "unknown" };

  const week = await getWeek(weekId);
  if (!week) return { ok: false, error: "unknown" };

  const res = await savePick(viewer.id, week, teamAbbr);
  if (!res.ok) return res;

  revalidatePath("/");
  revalidatePath("/season");
  revalidatePath("/pool");
  return { ok: true };
}
