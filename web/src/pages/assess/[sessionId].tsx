/**
 * Assessment workspace page — 3-panel split layout.
 *
 * Left: ChallengePanel (markdown requirements)
 * Center: Code editor + submission log
 * Right: SkillsRadarMap + SkillBarMeter + LevelBadge
 */
import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ChallengePanel } from "../../components/assessment/ChallengePanel";
import { CodeReviewStream } from "../../components/assessment/CodeReviewStream";
import { SkillsRadarMap, SkillBarMeter } from "../../components/assessment/SkillsRadarMap";
import { LevelBadge } from "../../components/assessment/LevelBadge";
import { EscalationGauge } from "../../components/assessment/EscalationGauge";
import { SubmissionHistory } from "../../components/assessment/SubmissionHistory";

const API_URL = "http://localhost:8000";

export default function AssessmentPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const [state, setState] = useState<any>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(true);

  // Auto-start session if demo
  useEffect(() => {
    if (sessionId === "demo") {
      fetch(`${API_URL}/api/assessment/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: "demo-engineer" }),
      })
        .then((r) => r.json())
        .then((data) => {
          navigate(`/assess/${data.session_id}`, { replace: true });
        });
      return;
    }

    // Load existing session state
    if (sessionId) {
      fetch(`${API_URL}/api/assessment/${sessionId}/state`)
        .then((r) => r.json())
        .then((data) => {
          if (data.detail) {
            // Session not found — auto-start
            fetch(`${API_URL}/api/assessment/start`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ user_id: "demo-engineer" }),
            })
              .then((r) => r.json())
              .then((d) => navigate(`/assess/${d.session_id}`, { replace: true }));
          } else {
            setState(data);
          }
        })
        .finally(() => setLoading(false));
    }
  }, [sessionId]);

  const handleSubmit = async () => {
    if (!sessionId || !code.trim()) return;
    setSubmitting(true);
    const res = await fetch(`${API_URL}/api/assessment/${sessionId}/submit`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        challenge_id: state?.active_challenge_id || "test",
        code,
        language: "typescript",
      }),
    });
    const data = await res.json();
    if (data.job_id) setJobId(data.job_id);
    setSubmitting(false);

    // Refresh state
    fetch(`${API_URL}/api/assessment/${sessionId}/state`)
      .then((r) => r.json())
      .then(setState);
  };

  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center bg-[#0a0a0a] text-neutral-500">
        Loading assessment...
      </div>
    );
  }

  return (
    <div className="h-screen flex bg-[#0a0a0a] text-neutral-100">
      {/* LEFT: Challenge */}
      <aside className="w-[360px] border-r border-neutral-800 flex-shrink-0 overflow-hidden">
        <ChallengePanel
          challenge={state?.challenge_data ?? null}
          isLoading={!state}
        />
      </aside>

      {/* CENTER: Code + Review */}
      <main className="flex-1 flex flex-col min-w-0">
        {/* Code editor + submit */}
        <div className="flex-1 overflow-hidden p-4 flex flex-col">
            <textarea
              className="flex-1 w-full bg-neutral-950 text-neutral-200 font-mono text-sm p-4 rounded border border-neutral-800 resize-none focus:outline-none focus:border-neutral-600"
              placeholder="Write your solution here..."
              value={code}
              onChange={(e) => setCode(e.target.value)}
              disabled={submitting}
            />
            <div className="flex items-center justify-between mt-3">
              <div className="flex items-center gap-3">
                <span className="text-xs text-neutral-600 font-mono">
                  {state?.current_level ?? "BASELINE"}
                </span>
              </div>
              <button
                className="px-6 py-2 bg-neutral-100 text-neutral-900 text-sm font-medium rounded hover:bg-white transition-colors disabled:opacity-50"
                onClick={handleSubmit}
                disabled={submitting || !sessionId || !code.trim()}
              >
              {submitting ? "Evaluating..." : "Submit"}
            </button>
          </div>
        </div>

        {/* Evaluation stream */}
        <div className="h-[250px] border-t border-neutral-800 overflow-hidden">
          <CodeReviewStream
            jobId={jobId}
            submittedCode=""
            language="typescript"
          />
        </div>
      </main>

      {/* RIGHT: Metrics */}
      <aside className="w-[400px] border-l border-neutral-800 flex-shrink-0 overflow-y-auto p-6 space-y-6">
        {/* Level badge */}
        <LevelBadge
          level={state?.current_level ?? "BASELINE"}
          escalationDepth={state?.escalation_depth ?? 0}
        />

        {/* Escalation gauge */}
        <EscalationGauge depth={state?.escalation_depth ?? 0} />

        {/* Radar chart */}
        <div>
          <h3 className="text-xs font-medium text-neutral-500 uppercase tracking-wide mb-3">
            Skills Radar
          </h3>
          <SkillsRadarMap skills={state?.skills_matrix ?? {}} size={240} />
        </div>

        {/* Bar meters */}
        <div>
          <h3 className="text-xs font-medium text-neutral-500 uppercase tracking-wide mb-3">
            Skill Breakdown
          </h3>
          <SkillBarMeter skills={state?.skills_matrix ?? {}} />
        </div>

        {/* Submission history */}
        <div>
          <h3 className="text-xs font-medium text-neutral-500 uppercase tracking-wide mb-3">
            Attempt History
          </h3>
          <SubmissionHistory history={state?.evaluation_history ?? []} />
        </div>
      </aside>
    </div>
  );
}
