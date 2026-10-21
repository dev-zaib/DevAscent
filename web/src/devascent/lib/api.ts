// Typed client for the DevAscent FastAPI backend (open CORS on :8000).
const API = "";

async function post<T>(path: string, body: unknown): Promise<T> {
  const r = await fetch(API + path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`${path} ${r.status}`);
  return r.json() as Promise<T>;
}
async function get<T>(path: string): Promise<T> {
  const r = await fetch(API + path);
  if (!r.ok) throw new Error(`${path} ${r.status}`);
  return r.json() as Promise<T>;
}

export interface RoadmapNode {
  id: string; label: string; tier: "foundation" | "core" | "advanced" | "elite";
  skill: string; deps: string[]; blurb: string;
  status: "available" | "learning" | "mastered"; score: number | null;
}
export interface Roadmap {
  title: string; nodes: RoadmapNode[]; edges: { from: string; to: string }[]; provider?: string;
}
export interface Lesson {
  concept: string; narration_script: string; key_points: string[]; approach_steps: string[];
  visual_kind: string; visual_spec: string; widget_html: string; study_terms: string[]; provider?: string;
}
export interface Question { id: number; type: string; prompt: string; what_we_look_for: string; }
export interface Grade { score: number; feedback: string; verdict: string; provider?: string; }
export interface CoachReport {
  summary: string; overall_mastery: number; momentum: number;
  strongest: [string, number][]; weakest: [string, number][];
  curriculum: { skill: string; band: string; recommended_action: string; due: boolean }[];
  milestones: string[]; total_evaluations: number;
}

export const api = {
  roadmap: (role: string, goal: string, user_id: string, skills_matrix: Record<string, number> = {}) =>
    post<Roadmap>("/api/roadmap", { role, goal, user_id, skills_matrix }),
  cachedRoadmap: (user_id: string) => get<Roadmap>(`/api/roadmap/${encodeURIComponent(user_id)}`),
  expand: (label: string, skill: string, blurb: string, user_id: string) =>
    post<Roadmap>("/api/roadmap/expand", { label, skill, blurb, user_id }),
  getExpansion: (user_id: string, key: string) =>
    get<Roadmap>(`/api/roadmap/expand/${encodeURIComponent(user_id)}/${encodeURIComponent(key)}`),
  lesson: (node: string, skill: string, user_id: string, regenerate = false, language = "javascript") =>
    post<Lesson>("/api/learn/lesson", { node, skill, language, user_id, regenerate }),
  interviewStart: (node: string, skill: string, count = 4, learned = "") =>
    post<{ questions: Question[]; provider?: string }>("/api/interview/start", { node, skill, count, learned }),
  assess: (user_id: string, count = 6) =>
    post<{ questions: Question[]; provider?: string; reason?: string }>("/api/interview/assess", { user_id, count }),
  markComplete: (user_id: string, skill: string, label: string, done = true) =>
    post<{ completed: Record<string, { label: string; ts: string }>; count: number }>("/api/progress/complete", { user_id, skill, label, done }),
  progress: (user_id: string) =>
    get<{ completed: Record<string, { label: string; ts: string }>; count: number }>(`/api/progress/${encodeURIComponent(user_id)}`),
  interviewGrade: (q: Question, answer: string, user_id: string, node: string, skill: string) =>
    post<Grade>("/api/interview/grade", {
      question: q.prompt, answer, what_we_look_for: q.what_we_look_for, user_id, node, skill,
    }),
  coach: (user_id: string) => get<CoachReport>(`/api/coach/progress/${encodeURIComponent(user_id)}`),
  tts: (text: string, voice = "am_michael") =>
    fetch("/api/tts", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, voice }),
    }),
};
