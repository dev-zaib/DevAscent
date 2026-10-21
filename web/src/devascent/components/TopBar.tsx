import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Map, ChevronDown, UserRound, Repeat } from "lucide-react";
import { type CoachReport } from "../lib/api";
import { loadProfile, clearProfile, getRecentProfiles, saveProfile, type Profile } from "../lib/store";

export default function TopBar({ coach, back }: { coach?: CoachReport | null; back?: boolean }) {
  const nav = useNavigate();
  const profile = loadProfile();
  const mastery = coach ? Math.round(coach.overall_mastery) : null;
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const h = (e: MouseEvent) => { if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false); };
    document.addEventListener("mousedown", h);
    return () => document.removeEventListener("mousedown", h);
  }, []);

  const recents = getRecentProfiles().filter((p) => p.user !== profile?.user);

  const switchTo = (p: Profile) => { saveProfile(p); setOpen(false); nav("/roadmap"); location.reload(); };
  const newHandle = () => { clearProfile(); setOpen(false); nav("/"); };

  return (
    <div style={{
      display: "flex", alignItems: "center", gap: 16, padding: "13px 22px",
      borderBottom: "1px solid var(--line)", background: "var(--surface)", flexShrink: 0,
    }}>
      <div onClick={() => nav("/roadmap")} title="Go to my roadmap"
        style={{ cursor: "pointer", fontWeight: 800, fontSize: 17, letterSpacing: "-0.02em" }}>
        Dev<span style={{ color: "var(--accent)" }}>Ascent</span>
      </div>
      {back && (
        <button className="btn sm ghost" onClick={() => nav("/roadmap")}>
          <Map size={15} /> Roadmap
        </button>
      )}
      <div style={{ flex: 1 }} />
      {coach && mastery != null && (
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{ textAlign: "right", lineHeight: 1.1 }}>
            <div className="eyebrow">Mastery</div>
            <div style={{ fontSize: 15, fontWeight: 700 }}>{mastery}/100</div>
          </div>
          <MasteryRing pct={mastery} />
        </div>
      )}

      {/* Profile menu — always reachable; switching is explicit & non-destructive. */}
      {profile && (
        <div ref={ref} style={{ position: "relative" }}>
          <button onClick={() => setOpen((o) => !o)}
            style={{
              display: "flex", alignItems: "center", gap: 9, height: 38, padding: "0 8px 0 8px",
              borderRadius: 99, border: "1px solid var(--line-2)", background: "var(--surface-2)",
            }}>
            <Avatar name={profile.user} />
            <span style={{ fontSize: 13.5, fontWeight: 600, maxWidth: 120, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{profile.user}</span>
            <ChevronDown size={15} color="var(--text-3)" />
          </button>

          {open && (
            <div className="fade-in" style={{
              position: "absolute", top: 46, right: 0, width: 256, zIndex: 30,
              background: "var(--surface)", border: "1px solid var(--line)", borderRadius: 14,
              boxShadow: "var(--shadow-lg)", padding: 8, overflow: "hidden",
            }}>
              <div style={{ padding: "10px 12px 12px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <Avatar name={profile.user} big />
                  <div style={{ minWidth: 0 }}>
                    <div style={{ fontSize: 14.5, fontWeight: 700, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{profile.user}</div>
                    <div style={{ fontSize: 11.5, color: "var(--text-3)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{profile.role}</div>
                  </div>
                </div>
              </div>
              <Item icon={<Map size={15} />} label="My roadmap" onClick={() => { setOpen(false); nav("/roadmap"); }} />
              {recents.length > 0 && (
                <>
                  <div className="eyebrow" style={{ padding: "10px 12px 6px" }}>Switch handle</div>
                  {recents.map((p) => (
                    <Item key={p.user} icon={<UserRound size={15} />} label={p.user} sub={p.role}
                      onClick={() => switchTo(p)} />
                  ))}
                </>
              )}
              <div style={{ height: 1, background: "var(--line)", margin: "6px 4px" }} />
              <Item icon={<Repeat size={15} />} label="New / different handle"
                sub="Your progress is saved per handle"
                onClick={newHandle} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function Item({ icon, label, sub, onClick }: { icon: React.ReactNode; label: string; sub?: string; onClick: () => void }) {
  return (
    <button onClick={onClick}
      style={{ display: "flex", alignItems: "center", gap: 10, width: "100%", padding: "9px 12px", borderRadius: 9, textAlign: "left", color: "var(--text)" }}
      onMouseEnter={(e) => (e.currentTarget.style.background = "var(--surface-sunk)")}
      onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}>
      <span style={{ color: "var(--text-3)", display: "flex" }}>{icon}</span>
      <span style={{ minWidth: 0 }}>
        <span style={{ display: "block", fontSize: 13.5, fontWeight: 500, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{label}</span>
        {sub && <span style={{ display: "block", fontSize: 11, color: "var(--text-3)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{sub}</span>}
      </span>
    </button>
  );
}

function Avatar({ name, big }: { name: string; big?: boolean }) {
  const s = big ? 36 : 26;
  return (
    <span style={{
      width: s, height: s, borderRadius: 99, flexShrink: 0, display: "grid", placeItems: "center",
      background: "var(--accent-tint)", color: "var(--accent)", fontWeight: 700, fontSize: big ? 15 : 12,
    }}>{(name[0] || "?").toUpperCase()}</span>
  );
}

function MasteryRing({ pct }: { pct: number }) {
  const r = 15, c = 2 * Math.PI * r;
  return (
    <svg width={38} height={38} viewBox="0 0 36 36">
      <circle cx="18" cy="18" r={r} fill="none" stroke="var(--line-2)" strokeWidth="3.2" />
      <circle cx="18" cy="18" r={r} fill="none" stroke="var(--accent)" strokeWidth="3.2" strokeLinecap="round"
        strokeDasharray={c} strokeDashoffset={c * (1 - pct / 100)} transform="rotate(-90 18 18)"
        style={{ transition: "stroke-dashoffset 1s var(--ease)" }} />
    </svg>
  );
}
