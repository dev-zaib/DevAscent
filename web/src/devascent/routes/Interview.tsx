import { useEffect, useState } from "react";
import { useParams, useLocation, useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "motion/react";
import { ArrowRight, Trophy, Map } from "lucide-react";
import { api, type Question, type Grade } from "../lib/api";
import { loadProfile } from "../lib/store";
import TopBar from "../components/TopBar";
import { AIThinking } from "../components/Loading";

function verdictColor(v: number) { return v >= 80 ? "var(--good)" : v >= 60 ? "var(--warn)" : "var(--bad)"; }

export default function Interview() {
  const { nodeId = "" } = useParams();
  const loc = useLocation();
  const nav = useNavigate();
  const profile = loadProfile();
  const st = (loc.state || {}) as { label?: string; skill?: string; learned?: string; assess?: boolean };
  const assessMode = st.assess || nodeId === "assess";
  const label = assessMode ? "What you've learned" : (st.label || decodeURIComponent(nodeId));
  const skill = st.skill || "";
  const learned = st.learned || "";

  const [qs, setQs] = useState<Question[]>([]);
  const [loading, setLoading] = useState(true);
  const [i, setI] = useState(0);
  const [answer, setAnswer] = useState("");
  const [grade, setGrade] = useState<Grade | null>(null);
  const [grading, setGrading] = useState(false);
  const [scores, setScores] = useState<number[]>([]);

  const [emptyReason, setEmptyReason] = useState("");
  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const r = assessMode
          ? await api.assess(profile?.user || "guest", 6)
          : await api.interviewStart(label, skill, 4, learned);
        if (alive) { setQs(r.questions); if (!r.questions.length) setEmptyReason((r as { reason?: string }).reason || "empty"); }
      } catch { /* */ }
      if (alive) setLoading(false);
    })();
    return () => { alive = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodeId]);

  const submit = async () => {
    if (answer.trim().length < 5 || !qs[i]) return;
    setGrading(true);
    try {
      const g = await api.interviewGrade(qs[i], answer, profile?.user || "anon", label, skill);
      setGrade(g); setScores((s) => [...s, g.score]);
    } catch { /* */ } finally { setGrading(false); }
  };
  const next = () => { setGrade(null); setAnswer(""); setI((x) => x + 1); };

  const done = !loading && qs.length > 0 && i >= qs.length;
  const avg = scores.length ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length) : 0;

  return (
    <div style={{ height: "100vh", display: "flex", flexDirection: "column" }}>
      <TopBar back />
      <div style={{ flex: 1, overflowY: "auto", display: "grid", placeItems: "center", padding: 24 }}>
        {loading ? (
          <AIThinking context={`Preparing your interview on ${label}`}
            steps={["Reviewing the topic", "Writing tough questions", "Setting the bar"]} />
        ) : qs.length === 0 ? (
          <div className="card" style={{ padding: 36, width: "min(460px,94vw)", textAlign: "center" }}>
            <div style={{ fontSize: 17, fontWeight: 700, marginBottom: 8 }}>Nothing to assess yet</div>
            <p style={{ color: "var(--text-2)", fontSize: 14, lineHeight: 1.6, marginBottom: 20 }}>
              {emptyReason === "no_completed_topics"
                ? "Mark some topics complete in their lessons, then I'll quiz you only on those."
                : "Learn and complete a topic first, then come back to be assessed."}
            </p>
            <button className="btn lg" style={{ width: "100%", justifyContent: "center" }} onClick={() => nav("/roadmap")}>
              <Map size={18} /> Back to roadmap
            </button>
          </div>
        ) : done ? (
          <motion.div className="card" initial={{ scale: 0.96, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
            style={{ padding: 36, width: "min(460px,94vw)", textAlign: "center" }}>
            <Trophy size={40} color="var(--accent)" style={{ margin: "0 auto 14px" }} />
            <div style={{ fontSize: 56, fontWeight: 800, color: verdictColor(avg), lineHeight: 1 }}>{avg}<span style={{ fontSize: 22, color: "var(--text-3)" }}>/100</span></div>
            <div className="eyebrow" style={{ marginTop: 8 }}>{avg >= 80 ? "Strong — node mastered" : avg >= 60 ? "Solid — keep refining" : "Foundations need work"}</div>
            <p style={{ color: "var(--text-2)", fontSize: 14, margin: "16px 0 22px", lineHeight: 1.6 }}>
              Your answers were graded and added to your skill matrix. Your roadmap updates accordingly.
            </p>
            <button className="btn lg" style={{ width: "100%", justifyContent: "center" }} onClick={() => nav("/roadmap")}>
              <Map size={18} /> Back to roadmap
            </button>
          </motion.div>
        ) : (
          <div style={{ width: "min(700px, 96vw)" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 14 }}>
              <span className="chip accent">{qs[i]?.type}</span>
              <span style={{ fontSize: 13, color: "var(--text-3)" }}>Question {i + 1} of {qs.length}</span>
              <div style={{ flex: 1, height: 5, background: "var(--surface-sunk)", borderRadius: 99, overflow: "hidden" }}>
                <div style={{ height: "100%", width: `${(i / qs.length) * 100}%`, background: "var(--accent)", transition: "width .4s" }} />
              </div>
            </div>
            <div className="card" style={{ padding: 24 }}>
              <h2 style={{ fontSize: 20, fontWeight: 700, lineHeight: 1.35, letterSpacing: "-0.01em" }}>{qs[i]?.prompt}</h2>
              <textarea value={answer} onChange={(e) => setAnswer(e.target.value)} disabled={!!grade}
                placeholder="Type your answer… be specific. Mention trade-offs and edge cases."
                style={{
                  width: "100%", minHeight: 170, marginTop: 16, padding: 14, fontSize: 14.5, lineHeight: 1.6,
                  borderRadius: 12, border: "1px solid var(--line-2)", background: "var(--surface-2)",
                  resize: "vertical", outline: "none", fontFamily: "inherit",
                }} />
              <AnimatePresence>
                {grade && (
                  <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }}
                    style={{ overflow: "hidden" }}>
                    <div style={{ marginTop: 16, padding: 16, borderRadius: 12, background: "var(--surface-sunk)", border: "1px solid var(--line)" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
                        <span style={{ fontSize: 26, fontWeight: 800, color: verdictColor(grade.score) }}>{Math.round(grade.score)}</span>
                        <span style={{ fontSize: 13, color: "var(--text-3)" }}>/100 · {grade.verdict}</span>
                      </div>
                      <p style={{ fontSize: 14, color: "var(--text-2)", lineHeight: 1.6 }}>{grade.feedback}</p>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
              <div style={{ display: "flex", justifyContent: "flex-end", gap: 10, marginTop: 18 }}>
                {!grade ? (
                  <button className="btn" disabled={grading || answer.trim().length < 5} onClick={submit}>
                    {grading ? <><span className="spin" /> Grading…</> : "Submit answer"}
                  </button>
                ) : (
                  <button className="btn" onClick={next}>
                    {i + 1 < qs.length ? <>Next question <ArrowRight size={16} /></> : <>See result <ArrowRight size={16} /></>}
                  </button>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
