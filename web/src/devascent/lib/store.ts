// Tiny persisted profile (handle, role, goal) across refresh.
const KEY = "devascent.profile.v1";

export interface Profile {
  user: string;
  role: string;
  goal: string;
}

export function loadProfile(): Profile | null {
  try { return JSON.parse(localStorage.getItem(KEY) || "null"); } catch { return null; }
}
export function saveProfile(p: Profile) {
  try { localStorage.setItem(KEY, JSON.stringify(p)); } catch { /* ignore */ }
}
export function clearProfile() {
  try { localStorage.removeItem(KEY); } catch { /* ignore */ }
}

// Recent handles — so a user can always jump back to a profile they've used.
// (Progress itself lives server-side in the journal, keyed by handle.)
const RECENTS = "devascent.recents.v1";

export function getRecentHandles(): string[] {
  try { return JSON.parse(localStorage.getItem(RECENTS) || "[]"); } catch { return []; }
}
export function rememberHandle(p: Profile) {
  try {
    const list: Profile[] = JSON.parse(localStorage.getItem(RECENTS + ".full") || "[]");
    const next = [p, ...list.filter((x) => x.user !== p.user)].slice(0, 6);
    localStorage.setItem(RECENTS + ".full", JSON.stringify(next));
    localStorage.setItem(RECENTS, JSON.stringify(next.map((x) => x.user)));
  } catch { /* ignore */ }
}
export function getRecentProfiles(): Profile[] {
  try { return JSON.parse(localStorage.getItem(RECENTS + ".full") || "[]"); } catch { return []; }
}

// Track which skills the user has already broken down (per handle), so the UI
// can show a "has sub-skills" marker and offer "Open" instead of regenerate.
const EXP = "devascent.expanded.";
export function markExpanded(user: string, skill: string) {
  try {
    const k = EXP + user; const s = new Set<string>(JSON.parse(localStorage.getItem(k) || "[]"));
    s.add(skill); localStorage.setItem(k, JSON.stringify([...s]));
  } catch { /* ignore */ }
}
export function getExpanded(user: string): Set<string> {
  try { return new Set<string>(JSON.parse(localStorage.getItem(EXP + user) || "[]")); } catch { return new Set(); }
}
