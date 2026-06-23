/**
 * BullMQ queue setup and job management for assessment evaluation.
 *
 * Jobs are enqueued from the API server and processed by worker processes.
 * The worker spawns a Python subprocess to run the LangGraph evaluation
 * pipeline and streams results back via Redis pub/sub for SSE delivery.
 */
import { Queue, Job } from "bullmq";

const REDIS_URL = process.env.REDIS_URL || "redis://localhost:6379";

export const evaluationQueue = new Queue("devascent-evaluations", {
  connection: { url: REDIS_URL },
  defaultJobOptions: {
    attempts: 3,
    backoff: { type: "exponential", delay: 5000 },
    timeout: 120_000,
    removeOnComplete: { age: 3600 },
    removeOnFail: { age: 86400 },
  },
});

export interface EvaluationJobData {
  sessionId: string;
  challengeId: string;
  code: string;
  language: string;
  userId: string;
}

export interface EvaluationResult {
  finalScore: number;
  rubricBreakdown: Record<string, number>;
  aiFeedback: string;
  nextAction: string;
  skillsMatrix: Record<string, number>;
  escalationDepth: number;
}

export async function enqueueEvaluation(
  data: EvaluationJobData,
): Promise<{ jobId: string }> {
  const job = await evaluationQueue.add("evaluate", data);
  return { jobId: job.id! };
}

export async function getJobResult(
  jobId: string,
): Promise<EvaluationResult | null> {
  const job = await Job.fromId(evaluationQueue, jobId);
  if (!job) return null;

  const state = await job.getState();
  if (state === "completed") {
    return job.returnvalue as EvaluationResult;
  }
  return null;
}
