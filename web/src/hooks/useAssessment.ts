/**
 * useAssessment hook — assessment session state management.
 *
 * Fetches assessment state, handles code submission,
 * and manages SSE connection for evaluation streaming.
 */
import { useState, useEffect, useCallback } from "react";
import { useSSE } from "./useSSE";

interface AssessmentState {
  current_level: string;
  skills_matrix: Record<string, number>;
  escalation_depth: number;
  challenge_attempt: number;
  evaluation_history: any[];
  active_challenge_id?: string;
  challenge_data?: any;
  next_action?: string;
}

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export function useAssessment(sessionId: string | null) {
  const [state, setState] = useState<AssessmentState | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sse = useSSE(jobId);

  // Fetch initial state
  useEffect(() => {
    if (!sessionId) return;

    fetch(`${API_URL}/api/assessment/${sessionId}/state`)
      .then((r) => r.json())
      .then(setState)
      .catch((e) => setError(e.message));
  }, [sessionId]);

  // React to evaluation completion
  useEffect(() => {
    if (sse.complete) {
      setSubmitting(false);
      // Refresh state after evaluation
      if (sessionId) {
        fetch(`${API_URL}/api/assessment/${sessionId}/state`)
          .then((r) => r.json())
          .then(setState);
      }
    }
  }, [sse.complete, sessionId]);

  const submitCode = useCallback(
    async (code: string, language: string) => {
      if (!sessionId) return;

      setSubmitting(true);
      setError(null);

      try {
        const res = await fetch(
          `${API_URL}/api/assessment/${sessionId}/submit`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              challenge_id: state?.active_challenge_id,
              code,
              language,
            }),
          },
        );

        if (res.ok) {
          const data = await res.json();
          setJobId(data.jobId);
        } else {
          const err = await res.json();
          setError(err.detail || "Submission failed");
          setSubmitting(false);
        }
      } catch (e: any) {
        setError(e.message);
        setSubmitting(false);
      }
    },
    [sessionId, state?.active_challenge_id],
  );

  return {
    state,
    jobId,
    submitCode,
    submitting,
    error,
    evaluationEvents: sse,
  };
}
