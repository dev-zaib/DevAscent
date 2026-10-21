import { useEffect, useRef, useState } from "react";
import { useParams, useLocation, useNavigate } from "react-router-dom";
import { motion } from "motion/react";
import { Play, Pause, Swords, BookOpen, RefreshCw, CheckCircle2, Check } from "lucide-react";
import { api, type Lesson } from "../lib/api";
import { loadProfile } from "../lib/store";
import { splitSentences, narrate, localVoiceAvailable, ttsSupported, type NarrationHandle } from "../lib/tts";
import TopBar from "../components/TopBar";
import { LessonSkeleton } from "../components/Loading";

// Base theme injected into every playground iframe so LLM-generated widgets
// look on-brand (Inter font, light warm bg, styled controls) regardless of
// what HTML the model returned.
const WIDGET_BASE = `<style>
  *{box-sizing:border-box}
  body{font-family:Inter,-apple-system,BlinkMacSystemFont,'Segoe UI',system-ui,sans-serif;
    background:#FBFAF7;color:#2B2A26;margin:0;padding:22px;line-height:1.5;
    -webkit-font-smoothing:antialiased;letter-spacing:-0.01em}
  h1,h2,h3,h4{letter-spacing:-0.02em;margin:0 0 10px}
  h3{font-size:16px;font-weight:700}
  p{color:#6B6862;margin:0 0 12px}
  label{font-size:13px;color:#6B6862}
  input,select,textarea{font-family:inherit;font-size:14px;color:#2B2A26;background:#fff;
    border:1px solid #DED9CC;border-radius:9px;padding:8px 11px;outline:none;transition:border-color .15s,box-shadow .15s}
  input:focus,select:focus,textarea:focus{border-color:#C96442;box-shadow:0 0 0 3px rgba(201,100,66,0.12)}
  button{font-family:inherit;font-size:13.5px;font-weight:600;color:#fff;background:#C96442;
    border:none;border-radius:9px;padding:9px 15px;cursor:pointer;transition:background .15s,transform .1s;margin:2px}
  button:hover{background:#B5563A}
  button:active{transform:translateY(1px)}
  button.secondary,.ghost{background:#F0EEE6;color:#2B2A26;border:1px solid #DED9CC}
  code,pre{font-family:'JetBrains Mono',ui-monospace,monospace;background:#F0EEE6;border-radius:6px;padding:2px 6px;font-size:13px}
  pre{padding:12px;overflow:auto}
  ::-webkit-scrollbar{width:8px;height:8px}::-webkit-scrollbar-thumb{background:#DED9CC;border-radius:99px}
</style>`;

export default function Studio() {
  const { nodeId = "" } = useParams();
  const loc = useLocation();
  const nav = useNavigate();
  const st = (loc.state || {}) as { label?: string; skill?: string };
  const label = st.label || decodeURIComponent(nodeId);
  const skill = st.skill || "";
  const user = loadProfile()?.user || "guest";

  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [loading, setLoading] = useState(true);
  const [regenerating, setRegenerating] = useState(false);
  const [done, setDone] = useState(false);
  const [sentences, setSentences] = useState<string[]>([]);
  const [active, setActive] = useState(-1);
  const [speaking, setSpeaking] = useState(false);
  const [rate, setRate] = useState(1);
  const [localVoice, setLocalVoice] = useState(false);
  const handleRef = useRef<NarrationHandle | null>(null);

  useEffect(() => { localVoiceAvailable().then(setLocalVoice); }, []);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const [l, prog] = await Promise.all([
          api.lesson(label, skill, user),
          api.progress(user).catch(() => ({ completed: {} as Record<string, unknown> })),
        ]);
        if (!alive) return;
        setLesson(l);
        setSentences(splitSentences(l.narration_script));
        setDone(!!(prog.completed && (prog.completed as Record<string, unknown>)[skill || label]));
      } catch { /* show error-free empty */ }
      if (alive) setLoading(false);
    })();
    return () => { alive = false; handleRef.current?.stop(); window.speechSynthesis?.cancel(); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodeId]);

  const regenerate = async () => {
    setRegenerating(true); handleRef.current?.stop(); setSpeaking(false); setActive(-1);
    try {
      const l = await api.lesson(label, skill, user, true);
      setLesson(l); setSentences(splitSentences(l.narration_script));
    } catch { /* keep current */ } finally { setRegenerating(false); }
  };

  const toggleDone = async () => {
    const next = !done; setDone(next);
    try { await api.markComplete(user, skill || label, label, next); } catch { setDone(!next); }
  };

  // Scope the interview to what THIS lesson taught.
  const learned = lesson ? `${lesson.concept}\nKey points:\n- ${lesson.key_points.join("\n- ")}` : "";
  const goProve = () => nav(`/interview/${encodeURIComponent(nodeId)}`,
    { state: { label, skill, learned } });

  const toggleSpeak = async () => {
    if (speaking) { handleRef.current?.stop(); setSpeaking(false); setActive(-1); return; }
    if (!ttsSupported() || sentences.length === 0) return;
    setSpeaking(true);
    handleRef.current = await narrate(sentences, setActive, () => { setSpeaking(false); setActive(-1); }, rate);
  };

  return (
    <div style={{ height: "100vh", display: "flex", flexDirection: "column" }}>
      <TopBar back />
      {loading ? (
        <LessonSkeleton context={`on ${label}`} />
      ) : !lesson ? (
        <Center>Couldn't load this lesson. Go back and try again.</Center>
      ) : (
        <div className="fade-in" style={{ flex: 1, display: "grid", gridTemplateColumns: "1.1fr 1fr", minHeight: 0 }}>
          {/* LEFT — narrated lesson */}
          <div style={{ overflowY: "auto", padding: 28, borderRight: "1px solid var(--line)" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
              <span className="eyebrow"><BookOpen size={12} style={{ verticalAlign: -2 }} /> Lesson</span>
              <div style={{ flex: 1 }} />
              <button className="btn sm ghost" onClick={regenerate} disabled={regenerating} title="Generate a fresh lesson">
                {regenerating ? <span className="spin" /> : <RefreshCw size={14} />} Regenerate
              </button>
              <button className="btn sm" onClick={toggleDone}
                style={done ? { background: "var(--good)" } : { background: "var(--surface-2)", color: "var(--text)", border: "1px solid var(--line-2)" }}>
                {done ? <><Check size={15} /> Completed</> : <><CheckCircle2 size={15} /> Mark complete</>}
              </button>
            </div>
            <h1 style={{ fontSize: 30, fontWeight: 800, letterSpacing: "-0.03em", marginBottom: 14 }}>{label}</h1>

            {/* narration controls */}
            <div className="card" style={{ display: "flex", alignItems: "center", gap: 14, padding: 14, marginBottom: 18 }}>
              <button className="btn" style={{ width: 46, height: 46, borderRadius: 99, padding: 0, justifyContent: "center" }}
                onClick={toggleSpeak} title={speaking ? "Pause narration" : "Read it to me"}>
                {speaking ? <Pause size={18} /> : <Play size={18} style={{ marginLeft: 2 }} />}
              </button>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 13.5, fontWeight: 600 }}>{speaking ? "Narrating…" : "Read it to me"}</div>
                <div style={{ fontSize: 11.5, color: "var(--text-3)" }}>
                  {localVoice ? "Natural local voice (Kokoro) · highlights as it reads"
                    : "Browser voice · run scripts/setup_tts.sh for a natural voice"}
                </div>
              </div>
              <select value={rate} onChange={(e) => setRate(Number(e.target.value))}
                style={{ height: 32, borderRadius: 8, border: "1px solid var(--line-2)", background: "var(--surface-2)", padding: "0 8px", fontSize: 12 }}>
                <option value={0.85}>0.85×</option><option value={1}>1×</option><option value={1.25}>1.25×</option><option value={1.5}>1.5×</option>
              </select>
            </div>

            {/* concept + narration body with highlight */}
            <p style={{ fontSize: 15.5, lineHeight: 1.7, color: "var(--text)", marginBottom: 18 }}>{lesson.concept}</p>
            <div style={{ fontSize: 15, lineHeight: 1.85, color: "var(--text-2)", marginBottom: 22 }}>
              {sentences.map((s, i) => (
                <span key={i} style={{
                  background: active === i ? "var(--accent-tint-2)" : "transparent",
                  color: active === i ? "var(--text)" : undefined,
                  borderRadius: 4, padding: active === i ? "1px 3px" : 0, transition: "background .2s",
                }}>{s} </span>
              ))}
            </div>

            <Section title="Key points">
              <ul style={{ listStyle: "none", display: "flex", flexDirection: "column", gap: 8 }}>
                {lesson.key_points.map((k, i) => (
                  <li key={i} style={{ display: "flex", gap: 9, fontSize: 14, color: "var(--text-2)", lineHeight: 1.5 }}>
                    <span style={{ color: "var(--accent)" }}>▸</span>{k}</li>
                ))}
              </ul>
            </Section>
            <Section title="How to apply it">
              <ol style={{ listStyle: "none", counterReset: "s", display: "flex", flexDirection: "column", gap: 9 }}>
                {lesson.approach_steps.map((s, i) => (
                  <li key={i} style={{ display: "flex", gap: 10, fontSize: 14, color: "var(--text-2)", lineHeight: 1.5 }}>
                    <span style={{ width: 21, height: 21, flexShrink: 0, borderRadius: 6, background: "var(--accent)", color: "#fff", fontSize: 11, fontWeight: 700, display: "grid", placeItems: "center" }}>{i + 1}</span>{s}</li>
                ))}
              </ol>
            </Section>
            {lesson.study_terms.length > 0 && (
              <Section title="Go deeper">
                <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                  {lesson.study_terms.map((t, i) => <span key={i} className="chip">{t}</span>)}
                </div>
              </Section>
            )}
            <button className="btn lg" style={{ marginTop: 26, width: "100%", justifyContent: "center" }}
              onClick={goProve}>
              <Swords size={18} /> Ready? Prove it — quiz on this lesson
            </button>
          </div>

          {/* RIGHT — visual + playable */}
          <div style={{ overflowY: "auto", padding: 28, display: "flex", flexDirection: "column", gap: 18 }}>
            <MermaidView code={lesson.visual_spec} fallback={buildFallbackDiagram(label, lesson.key_points)} />
            <div style={{ flex: 1, minHeight: 320, display: "flex", flexDirection: "column" }}>
              <div className="eyebrow" style={{ marginBottom: 10 }}>Play with it</div>
              {lesson.widget_html ? (
                <iframe title="playground" sandbox="allow-scripts" srcDoc={WIDGET_BASE + lesson.widget_html}
                  style={{ flex: 1, width: "100%", minHeight: 320, border: "1px solid var(--line)", borderRadius: 16, background: "var(--surface-2)", boxShadow: "var(--shadow-sm)" }} />
              ) : (
                <div className="card" style={{ display: "grid", placeItems: "center", flex: 1, color: "var(--text-3)", fontSize: 13 }}>No interactive widget for this lesson.</div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: 20 }}>
      <div className="eyebrow" style={{ marginBottom: 10 }}>{title}</div>
      {children}
    </div>
  );
}
function Center({ children }: { children: React.ReactNode }) {
  return <div style={{ display: "grid", placeItems: "center", flex: 1, color: "var(--text-2)", fontSize: 15, textAlign: "center", padding: 24 }}><div>{children}</div></div>;
}

// Concept map is REQUIRED: try the model's diagram, fall back to one built
// from the key points so a map always renders.
function buildFallbackDiagram(label: string, keyPoints: string[]): string {
  const clean = (s: string) => s.replace(/["\(\)\[\];:]/g, "").replace(/\s+/g, " ").trim().slice(0, 38);
  const root = clean(label) || "Concept";
  const pts = (keyPoints.length ? keyPoints : ["Idea", "Apply it", "Practice"]).slice(0, 6);
  const lines = [`graph TD`, `  R["${root}"]`];
  pts.forEach((p, i) => lines.push(`  R --> N${i}["${clean(p)}"]`));
  return lines.join("\n");
}

function MermaidView({ code, fallback }: { code: string; fallback: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const [state, setState] = useState<"loading" | "ok" | "err">("loading");
  useEffect(() => {
    let alive = true;
    (async () => {
      const mermaid = (await import("mermaid")).default;
      mermaid.initialize({ startOnLoad: false, theme: "base", themeVariables: {
        background: "#FBFAF7", primaryColor: "#FFFFFF", primaryBorderColor: "#C96442",
        primaryTextColor: "#2B2A26", lineColor: "#B5B0A2", fontFamily: "Inter, sans-serif",
      } });
      const candidates = [code, fallback].filter(Boolean).map((c) => c.trim());
      for (let k = 0; k < candidates.length; k++) {
        try {
          const id = "m" + k + Math.abs(candidates[k].length * 7);
          const { svg } = await mermaid.render(id, candidates[k]);
          if (alive && ref.current) { ref.current.innerHTML = svg; setState("ok"); }
          return;
        } catch { /* try next candidate */ }
      }
      if (alive) setState("err");
    })();
    return () => { alive = false; };
  }, [code, fallback]);
  return (
    <div>
      <div className="eyebrow" style={{ marginBottom: 10 }}>Concept map</div>
      {state === "loading" && <div className="skeleton" style={{ height: 150, borderRadius: 16 }} />}
      <div className="card" style={{ padding: 18, display: state === "ok" ? "grid" : "none", placeItems: "center" }}>
        <div ref={ref} style={{ width: "100%" }} />
      </div>
      {state === "err" && (
        <div className="card" style={{ padding: 18, color: "var(--text-3)", fontSize: 13 }}>Diagram unavailable.</div>
      )}
    </div>
  );
}
