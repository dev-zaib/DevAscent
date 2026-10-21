import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "motion/react";
import { ArrowRight, Sparkles, GraduationCap, Mic, Gamepad2 } from "lucide-react";
import { loadProfile, saveProfile, rememberHandle, getRecentProfiles, type Profile } from "../lib/store";

const ROLES = [
  "Student / self-taught",
  "Junior engineer",
  "Mid-level engineer",
  "Senior engineer",
  "Switching into backend",
];

export default function Onboard() {
  const nav = useNavigate();
  const [user, setUser] = useState("");
  const [role, setRole] = useState("Mid-level engineer");
  const [goal, setGoal] = useState("Become a top 1% engineer");
  const [recents, setRecents] = useState<Profile[]>([]);

  useEffect(() => {
    const p = loadProfile();
    if (p) { setUser(p.user); setRole(p.role); setGoal(p.goal); }
    setRecents(getRecentProfiles());
  }, []);

  const begin = (override?: Profile) => {
    const p = override || { user: user.trim() || "climber", role, goal };
    saveProfile(p);
    rememberHandle(p);
    nav("/roadmap");
  };

  return (
    <div style={{ minHeight: "100vh", display: "grid", placeItems: "center", padding: 24 }}>
      <motion.div
        className="fade-in"
        style={{ width: "min(560px, 94vw)", textAlign: "center" }}
      >
        <div className="eyebrow" style={{ marginBottom: 18 }}>DevAscent</div>
        <h1 style={{ fontSize: "clamp(36px, 6vw, 58px)", fontWeight: 800, lineHeight: 1.04, letterSpacing: "-0.03em" }}>
          Your path to the<br /><span style={{ color: "var(--accent)" }}>top 1%</span>, mapped.
        </h1>
        <p style={{ color: "var(--text-2)", fontSize: 17, lineHeight: 1.6, margin: "18px auto 30px", maxWidth: 420 }}>
          Tell me where you are. I'll build a personalized roadmap, teach each skill with
          interactive, narrated lessons, and grill you with real interviews until you've mastered it.
        </p>

        {recents.length > 0 && (
          <div className="card" style={{ padding: 16, textAlign: "left", marginBottom: 14 }}>
            <label className="eyebrow">Continue as</label>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 10 }}>
              {recents.map((p) => (
                <button key={p.user} onClick={() => begin(p)} className="chip"
                  style={{ cursor: "pointer", padding: "7px 13px", fontSize: 13, display: "inline-flex", alignItems: "center", gap: 7 }}>
                  <span style={{ width: 20, height: 20, borderRadius: 99, background: "var(--accent-tint)", color: "var(--accent)", fontWeight: 700, fontSize: 11, display: "grid", placeItems: "center" }}>{p.user[0]?.toUpperCase()}</span>
                  {p.user}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="card" style={{ padding: 22, textAlign: "left" }}>
          <label className="eyebrow">Your handle</label>
          <input className="field" style={{ margin: "8px 0 18px" }} value={user}
            placeholder="pick a handle…" autoFocus
            onChange={(e) => setUser(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && begin()} />

          <label className="eyebrow">Where are you now?</label>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8, margin: "10px 0 18px" }}>
            {ROLES.map((r) => (
              <button key={r} onClick={() => setRole(r)}
                className="chip" style={{
                  cursor: "pointer", padding: "7px 13px", fontSize: 13,
                  background: role === r ? "var(--accent-tint)" : "var(--surface-sunk)",
                  color: role === r ? "var(--accent)" : "var(--text-2)",
                  borderColor: role === r ? "transparent" : "var(--line)",
                  fontWeight: role === r ? 600 : 500,
                }}>{r}</button>
            ))}
          </div>

          <label className="eyebrow">Your goal</label>
          <input className="field" style={{ marginTop: 8 }} value={goal}
            onChange={(e) => setGoal(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && begin()} />

          <button className="btn lg" style={{ width: "100%", justifyContent: "center", marginTop: 20 }} onClick={() => begin()}>
            Build my roadmap <ArrowRight size={18} />
          </button>
        </div>

        <div style={{ display: "flex", gap: 22, justifyContent: "center", marginTop: 22, color: "var(--text-3)", fontSize: 13, flexWrap: "wrap" }}>
          <Feat icon={<Sparkles size={15} />} t="AI roadmap" />
          <Feat icon={<GraduationCap size={15} />} t="Interactive lessons" />
          <Feat icon={<Mic size={15} />} t="Narrated" />
          <Feat icon={<Gamepad2 size={15} />} t="Playable" />
        </div>
      </motion.div>
    </div>
  );
}

function Feat({ icon, t }: { icon: React.ReactNode; t: string }) {
  return <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>{icon}{t}</span>;
}
