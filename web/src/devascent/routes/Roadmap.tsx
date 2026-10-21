import { useEffect, useMemo, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import ReactFlow, { Background, Controls, type Node, type Edge, Handle, Position } from "reactflow";
import dagre from "dagre";
import { motion, AnimatePresence } from "motion/react";
import { GraduationCap, Swords, X, Check, Lock, Layers } from "lucide-react";
import { api, type Roadmap as RoadmapT, type RoadmapNode, type CoachReport } from "../lib/api";
import { loadProfile, markExpanded, getExpanded } from "../lib/store";
import TopBar from "../components/TopBar";
import { AIThinking } from "../components/Loading";

const TIERS = ["foundation", "core", "advanced", "elite"] as const;
const TIER_META: Record<string, { c: string; tint: string; label: string }> = {
  foundation: { c: "#C96442", tint: "rgba(201,100,66,0.10)", label: "Foundation" },
  core: { c: "#5B7CC9", tint: "rgba(91,124,201,0.10)", label: "Core" },
  advanced: { c: "#8A6EC9", tint: "rgba(138,110,201,0.10)", label: "Advanced" },
  elite: { c: "#C9A33A", tint: "rgba(201,163,58,0.12)", label: "Elite" },
};
const TIER_LABEL: Record<string, string> = Object.fromEntries(
  Object.entries(TIER_META).map(([k, v]) => [k, v.label]),
);
const NODE_W = 226;
const NODE_H = 128;
const clamp2: React.CSSProperties = {
  display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical",
  overflow: "hidden", textOverflow: "ellipsis",
};

function SkillNodeView({ data }: { data: RoadmapNode & { expanded?: boolean; done?: boolean; onClick: () => void } }) {
  const tier = TIER_META[data.tier] || TIER_META.core;
  const mastered = data.status === "mastered";
  const learning = data.status === "learning";
  const done = data.done;
  return (
    <div onClick={data.onClick}
      style={{
        width: NODE_W, height: NODE_H, position: "relative", cursor: "pointer",
        background: "var(--surface-2)", borderRadius: 16, overflow: "hidden",
        border: done ? "1px solid var(--good)" : "1px solid var(--line)", boxShadow: "var(--shadow-sm)",
        transition: "transform .16s var(--ease), box-shadow .2s",
        display: "flex", flexDirection: "column",
      }}
      onMouseEnter={(e) => { e.currentTarget.style.transform = "translateY(-3px)"; e.currentTarget.style.boxShadow = "var(--shadow-lg)"; }}
      onMouseLeave={(e) => { e.currentTarget.style.transform = "none"; e.currentTarget.style.boxShadow = "var(--shadow-sm)"; }}>
      <Handle type="target" position={Position.Left} style={{ opacity: 0, border: 0 }} />
      {/* tier accent strip */}
      <span style={{ position: "absolute", left: 0, top: 0, bottom: 0, width: 4, background: tier.c }} />
      <div style={{ padding: "12px 14px 12px 17px", display: "flex", flexDirection: "column", height: "100%" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 7, marginBottom: 7 }}>
          <span style={{ fontSize: 9.5, fontWeight: 700, letterSpacing: ".09em", textTransform: "uppercase",
            color: tier.c, background: tier.tint, padding: "2px 7px", borderRadius: 99 }}>{tier.label}</span>
          <span style={{ flex: 1 }} />
          {done ? <span style={{ display: "inline-flex", alignItems: "center", gap: 3, fontSize: 9.5, fontWeight: 700, color: "var(--good)", background: "var(--good-tint)", padding: "2px 6px", borderRadius: 99 }}><Check size={11} /> DONE</span>
            : mastered ? <Check size={14} color="var(--good)" />
            : learning ? <span style={{ width: 7, height: 7, borderRadius: 99, background: tier.c }} />
            : <Lock size={11} color="var(--text-3)" />}
        </div>
        <div style={{ fontSize: 14.5, fontWeight: 650, lineHeight: 1.25, letterSpacing: "-0.01em", ...clamp2 }}>{data.label}</div>
        <div style={{ fontSize: 11.5, color: "var(--text-3)", lineHeight: 1.4, marginTop: 4, ...clamp2 }}>{data.blurb}</div>
        <span style={{ flex: 1 }} />
        {data.score != null && data.score > 0 ? (
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <div style={{ flex: 1, height: 5, borderRadius: 99, background: "var(--surface-sunk)", overflow: "hidden" }}>
              <div style={{ height: "100%", width: `${data.score}%`, background: mastered ? "var(--good)" : tier.c }} />
            </div>
            <span style={{ fontSize: 10.5, fontFamily: "var(--mono)", color: "var(--text-3)" }}>{Math.round(data.score)}</span>
          </div>
        ) : data.expanded ? (
          <div style={{ fontSize: 11, fontWeight: 600, color: tier.c, display: "flex", alignItems: "center", gap: 5 }}>
            <Layers size={12} /> View sub-skills →
          </div>
        ) : (
          <div style={{ fontSize: 11, fontWeight: 600, color: tier.c, opacity: 0.9 }}>Start →</div>
        )}
      </div>
      <Handle type="source" position={Position.Right} style={{ opacity: 0, border: 0 }} />
    </div>
  );
}
const nodeTypes = { skill: SkillNodeView };

export default function Roadmap() {
  const nav = useNavigate();
  // Deep-link safe: fall back to a sensible default profile instead of bouncing.
  const profile = loadProfile() || { user: "guest", role: "Self-taught", goal: "Become a top 1% engineer" };
  const [graph, setGraph] = useState<RoadmapT | null>(null);
  const [coach, setCoach] = useState<CoachReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [sel, setSel] = useState<RoadmapNode | null>(null);
  // Drill-down stack: each level is a sub-roadmap of the node above it.
  const [drill, setDrill] = useState<{ label: string; graph: RoadmapT }[]>([]);
  const [expanding, setExpanding] = useState(false);
  const [expanded, setExpanded] = useState<Set<string>>(() => getExpanded(profile.user));
  const [completed, setCompleted] = useState<Set<string>>(new Set());
  const active = drill.length ? drill[drill.length - 1].graph : graph;

  useEffect(() => {
    let alive = true;
    (async () => {
      // Cache-first: instant repeat loads; generate only when empty.
      try {
        const cached = await api.cachedRoadmap(profile.user);
        if (alive && cached && cached.nodes && cached.nodes.length) { setGraph(cached); setLoading(false); }
      } catch { /* no cache yet */ }
      try {
        const g = await api.roadmap(profile.role, profile.goal, profile.user);
        if (alive && g.nodes?.length) setGraph(g);
      } catch { /* keep any cached graph */ }
      try { const c = await api.coach(profile.user); if (alive) setCoach(c); } catch { /* optional */ }
      try {
        const pr = await api.progress(profile.user);
        if (alive) setCompleted(new Set(Object.keys(pr.completed || {})));
      } catch { /* optional */ }
      if (alive) setLoading(false);
    })();
    return () => { alive = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Already-expanded node → drill straight in. Otherwise open the drawer.
  const open = useCallback((n: RoadmapNode) => {
    if (getExpanded(profile.user).has(n.skill)) doExpand(n);
    else setSel(n);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const doExpand = useCallback(async (n: RoadmapNode) => {
    setSel(null); setExpanding(true);
    try {
      const sub = await api.expand(n.label, n.skill, n.blurb, profile.user);
      if (sub?.nodes?.length) {
        setDrill((d) => [...d, { label: n.label, graph: sub }]);
        markExpanded(profile.user, n.skill);
        setExpanded((s) => new Set(s).add(n.skill));
      }
    } catch { /* ignore */ } finally { setExpanding(false); }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  const popTo = (i: number) => setDrill((d) => d.slice(0, i));

  const { rfNodes, rfEdges } = useMemo(() => {
    if (!active) return { rfNodes: [] as Node[], rfEdges: [] as Edge[] };
    const graph = active;
    const ids = new Set(graph.nodes.map((n) => n.id));
    const validEdges = graph.edges.filter((e) => ids.has(e.from) && ids.has(e.to));

    // Layered left→right layout via dagre: ranks by dependency depth, with
    // crossing minimization so connectors never run through cards.
    const g = new dagre.graphlib.Graph();
    g.setGraph({ rankdir: "LR", nodesep: 30, ranksep: 96, marginx: 24, marginy: 24, ranker: "tight-tree" });
    g.setDefaultEdgeLabel(() => ({}));
    graph.nodes.forEach((n) => g.setNode(n.id, { width: NODE_W, height: NODE_H }));
    validEdges.forEach((e) => g.setEdge(e.from, e.to));
    dagre.layout(g);

    const nodes: Node[] = graph.nodes.map((n) => {
      const p = g.node(n.id);
      return {
        id: n.id, type: "skill",
        position: { x: (p?.x ?? 0) - NODE_W / 2, y: (p?.y ?? 0) - NODE_H / 2 },
        data: { ...n, expanded: expanded.has(n.skill), done: completed.has(n.skill), onClick: () => open(n) },
        draggable: false,
        sourcePosition: Position.Right, targetPosition: Position.Left,
      };
    });
    const edges: Edge[] = validEdges.map((e, i) => ({
      id: `e${i}`, source: e.from, target: e.to, type: "bezier",
      style: { stroke: "rgba(150,140,128,0.5)", strokeWidth: 1.6 }, animated: false,
    }));
    return { rfNodes: nodes, rfEdges: edges };
  }, [active, open, expanded, completed]);

  return (
    <div style={{ height: "100vh", display: "flex", flexDirection: "column" }}>
      <TopBar coach={coach} />
      <div style={{ display: "flex", alignItems: "baseline", gap: 10, padding: "14px 24px 6px", flexWrap: "wrap" }}>
        {/* Breadcrumb: Roadmap › sub › sub */}
        <span onClick={() => popTo(0)} style={{ cursor: drill.length ? "pointer" : "default", fontSize: 19, fontWeight: 700, letterSpacing: "-0.02em", color: drill.length ? "var(--text-3)" : "var(--text)" }}>
          {drill.length ? "Roadmap" : (graph?.title || "Your roadmap")}
        </span>
        {drill.map((d, i) => (
          <span key={i} style={{ display: "inline-flex", alignItems: "baseline", gap: 10 }}>
            <span style={{ color: "var(--text-3)", fontSize: 16 }}>›</span>
            <span onClick={() => popTo(i + 1)}
              style={{ cursor: i < drill.length - 1 ? "pointer" : "default", fontSize: 19, fontWeight: 700, letterSpacing: "-0.02em",
                color: i < drill.length - 1 ? "var(--text-3)" : "var(--text)" }}>{d.label}</span>
          </span>
        ))}
        <span style={{ fontSize: 13, color: "var(--text-3)" }}>{active ? `${active.nodes.length} skills` : ""}</span>
        <div style={{ flex: 1 }} />
        <button className="btn sm" onClick={() => nav("/interview/assess", { state: { assess: true } })}
          title="Get quizzed only on topics you've completed"
          style={completed.size ? {} : { opacity: 0.55 }}>
          <Swords size={15} /> Assess what I've learned{completed.size ? ` (${completed.size})` : ""}
        </button>
        {TIERS.map((t) => (
          <span key={t} className="chip" style={{ fontSize: 11, gap: 6 }}>
            <span style={{ width: 8, height: 8, borderRadius: 99, background: TIER_META[t].c }} />
            {TIER_LABEL[t]}
          </span>
        ))}
      </div>

      <div style={{ flex: 1, position: "relative", minHeight: 0 }}>
        {loading ? (
          <div style={{ display: "grid", placeItems: "center", height: "100%" }}>
            <AIThinking context={`Mapping your path to ${profile.goal}`}
              steps={["Assessing your level", "Selecting the skills that matter", "Ordering by dependencies", "Drawing your roadmap"]} />
          </div>
        ) : (
          <ReactFlow nodes={rfNodes} edges={rfEdges} nodeTypes={nodeTypes}
            fitView fitViewOptions={{ padding: 0.2 }} proOptions={{ hideAttribution: true }}
            nodesDraggable={false} nodesConnectable={false} elementsSelectable
            style={{ background: "var(--bg)" }}>
            <Background color="var(--line-2)" gap={26} size={1} />
            <Controls showInteractive={false} />
          </ReactFlow>
        )}

        {expanding && (
          <div style={{ position: "absolute", inset: 0, display: "grid", placeItems: "center", background: "rgba(245,244,238,0.7)", backdropFilter: "blur(3px)", zIndex: 20 }}>
            <AIThinking context="Breaking this skill into a deeper sub-plan"
              steps={["Decomposing the topic", "Ordering sub-skills", "Building the sub-roadmap"]} />
          </div>
        )}

        <AnimatePresence>
          {sel && (
            <motion.div
              initial={{ x: 380, opacity: 0 }} animate={{ x: 0, opacity: 1 }} exit={{ x: 380, opacity: 0 }}
              transition={{ type: "spring", stiffness: 320, damping: 32 }}
              style={{
                position: "absolute", top: 0, right: 0, bottom: 0, width: "min(360px, 92vw)",
                background: "var(--surface)", borderLeft: "1px solid var(--line)",
                boxShadow: "var(--shadow-lg)", padding: 24, overflowY: "auto",
              }}>
              <button onClick={() => setSel(null)}
                style={{ position: "absolute", top: 16, right: 16, color: "var(--text-3)" }}><X size={20} /></button>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                <StatusPill status={sel.status} />
                <span className="chip" style={{ fontSize: 11 }}>{TIER_LABEL[sel.tier] || sel.tier}</span>
              </div>
              <h3 style={{ fontSize: 22, fontWeight: 700, letterSpacing: "-0.02em", margin: "6px 0 8px" }}>{sel.label}</h3>
              <p style={{ color: "var(--text-2)", fontSize: 14.5, lineHeight: 1.6 }}>{sel.blurb}</p>
              {sel.score != null && sel.score > 0 && (
                <div style={{ margin: "16px 0", fontSize: 13, color: "var(--text-2)" }}>
                  Mastery: <b style={{ color: statusColor(sel.status) }}>{Math.round(sel.score)}/100</b>
                </div>
              )}
              <div style={{ display: "flex", flexDirection: "column", gap: 10, marginTop: 22 }}>
                <button className="btn lg" style={{ justifyContent: "center" }}
                  onClick={() => doExpand(sel)}>
                  <Layers size={18} /> {expanded.has(sel.skill) ? "Open sub-skills" : "Break into sub-skills"}
                </button>
                <div style={{ display: "flex", gap: 10 }}>
                  <button className="btn ghost" style={{ flex: 1, justifyContent: "center" }}
                    onClick={() => nav(`/learn/${encodeURIComponent(sel.id)}`, { state: { label: sel.label, skill: sel.skill } })}>
                    <GraduationCap size={17} /> Learn
                  </button>
                  <button className="btn ghost" style={{ flex: 1, justifyContent: "center" }}
                    onClick={() => nav(`/interview/${encodeURIComponent(sel.id)}`, { state: { label: sel.label, skill: sel.skill } })}>
                    <Swords size={17} /> Prove
                  </button>
                </div>
                <p style={{ fontSize: 11.5, color: "var(--text-3)", textAlign: "center", lineHeight: 1.5, marginTop: 2 }}>
                  Broad topic? Break it down first. Learn &amp; Prove work best on focused sub-skills.
                </p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

function StatusPill({ status }: { status: string }) {
  if (status === "mastered") return <span className="chip" style={{ color: "var(--good)", background: "var(--good-tint)", borderColor: "transparent" }}><Check size={12} /> Mastered</span>;
  if (status === "learning") return <span className="chip accent">In progress</span>;
  return <span className="chip"><Lock size={11} /> Not started</span>;
}
