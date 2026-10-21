import { useEffect, useState } from "react";

// "AI agent is doing something" indicator — pulsing orb + cycling status.
export function AIThinking({ context, steps }: { context: string; steps?: string[] }) {
  const phases = steps && steps.length ? steps : ["Thinking", "Researching", "Designing", "Writing it up"];
  const [i, setI] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setI((x) => (x + 1) % phases.length), 1600);
    return () => clearInterval(t);
  }, [phases.length]);
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 16 }}>
      <div className="ai-orb"><i /><i /><i /><b /></div>
      <div style={{ textAlign: "center" }}>
        <div style={{ fontSize: 15, fontWeight: 600, color: "var(--text)" }}>
          <span className="dots">{phases[i]}</span>
        </div>
        <div style={{ fontSize: 13, color: "var(--text-3)", marginTop: 4 }}>{context}</div>
      </div>
    </div>
  );
}

export function SkelLine({ w = "100%", h = 14, mb = 10 }: { w?: string | number; h?: number; mb?: number }) {
  return <div className="skeleton" style={{ width: w, height: h, marginBottom: mb }} />;
}

export function SkelBlock({ h = 120, mb = 16 }: { h?: number; mb?: number }) {
  return <div className="skeleton" style={{ width: "100%", height: h, marginBottom: mb, borderRadius: 16 }} />;
}

// Lesson skeleton with an AI-thinking overlay — mirrors the real layout.
export function LessonSkeleton({ context }: { context: string }) {
  return (
    <div style={{ flex: 1, display: "grid", gridTemplateColumns: "1.1fr 1fr", minHeight: 0 }}>
      <div style={{ padding: 28, borderRight: "1px solid var(--line)", position: "relative" }}>
        <SkelLine w={70} h={11} mb={14} />
        <SkelLine w="60%" h={30} mb={20} />
        <SkelBlock h={70} />
        <SkelLine w="95%" /><SkelLine w="100%" /><SkelLine w="85%" mb={22} />
        <SkelLine w={90} h={11} mb={14} />
        <SkelLine w="80%" /><SkelLine w="70%" /><SkelLine w="75%" />
      </div>
      <div style={{ padding: 28, position: "relative" }}>
        <div style={{
          position: "absolute", inset: 0, display: "grid", placeItems: "center", zIndex: 2,
        }}>
          <AIThinking context={context} steps={["Researching the topic", "Writing the lesson", "Designing a visual", "Building a playground"]} />
        </div>
        <div style={{ opacity: 0.4 }}>
          <SkelBlock h={180} />
          <SkelBlock h={260} />
        </div>
      </div>
    </div>
  );
}
