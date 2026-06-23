/**
 * SSE client hook — connects to assessment evaluation stream.
 *
 * Handles reconnection with exponential backoff, parses typed events,
 * and exposes state for React components to consume.
 */
import { useState, useEffect, useRef, useCallback } from "react";

interface SSEMessage {
  stage: string;
  message: string;
  timestamp: string;
}

interface RubricEvent {
  dimension: string;
  score: number;
  maxScore: number;
  feedback: string;
}

interface SkillsUpdate {
  skillsMatrix: Record<string, number>;
}

interface CompleteEvent {
  finalScore: number;
  nextAction: string;
  message: string;
}

interface ErrorEvent {
  code: string;
  message: string;
}

export function useSSE(jobId: string | null) {
  const [connected, setConnected] = useState(false);
  const [progress, setProgress] = useState<SSEMessage | null>(null);
  const [rubricEvents, setRubricEvents] = useState<RubricEvent[]>([]);
  const [skillsMatrix, setSkillsMatrix] = useState<Record<string, number>>({});
  const [complete, setComplete] = useState<CompleteEvent | null>(null);
  const [error, setError] = useState<ErrorEvent | null>(null);
  const retryRef = useRef(0);

  const disconnect = useCallback(() => {
    setConnected(false);
  }, []);

  useEffect(() => {
    if (!jobId) return;

    const baseUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
    const url = `${baseUrl}/api/assessment/stream/${jobId}`;

    const eventSource = new EventSource(url);

    eventSource.onopen = () => {
      setConnected(true);
      retryRef.current = 0;
    };

    eventSource.addEventListener("progress", (e: MessageEvent) => {
      setProgress(JSON.parse(e.data));
    });

    eventSource.addEventListener("rubric", (e: MessageEvent) => {
      setRubricEvents((prev) => [...prev, JSON.parse(e.data)]);
    });

    eventSource.addEventListener("skills_update", (e: MessageEvent) => {
      setSkillsMatrix(JSON.parse(e.data).skillsMatrix);
    });

    eventSource.addEventListener("complete", (e: MessageEvent) => {
      setComplete(JSON.parse(e.data));
      eventSource.close();
    });

    eventSource.addEventListener("error", (e: MessageEvent) => {
      if (e.data) {
        setError(JSON.parse(e.data));
      }
    });

    eventSource.onerror = () => {
      eventSource.close();
      setConnected(false);

      const delay = Math.min(1000 * Math.pow(2, retryRef.current), 30000);
      retryRef.current += 1;

      if (retryRef.current <= 5) {
        setTimeout(() => {
          setConnected(true);
        }, delay);
      }
    };

    return () => {
      eventSource.close();
    };
  }, [jobId]);

  return {
    connected,
    progress,
    rubricEvents,
    skillsMatrix,
    complete,
    error,
    disconnect,
  };
}
