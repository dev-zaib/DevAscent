/**
 * Evaluation worker — processes assessment jobs from BullMQ queue.
 *
 * Spawns a Python subprocess that runs the LangGraph evaluation pipeline.
 * Results are streamed via Redis pub/sub for SSE delivery to the frontend.
 */
import { Worker, Job } from "bullmq";
import { spawn } from "child_process";
import type { EvaluationJobData, EvaluationResult } from "../src/lib/queue";

const REDIS_URL = process.env.REDIS_URL || "redis://localhost:6379";
const PYTHON_CMD = process.env.DEVASCENT_PYTHON || "python3";

async function runPythonEvaluation(
  data: EvaluationJobData,
): Promise<EvaluationResult> {
  return new Promise((resolve, reject) => {
    const child = spawn(PYTHON_CMD, [
      "-m",
      "devascent.assessment.run",
      "--session-id",
      data.sessionId,
      "--challenge-id",
      data.challengeId,
      "--code",
      data.code,
      "--language",
      data.language,
      "--user-id",
      data.userId,
      "--json",
    ]);

    let stdout = "";
    let stderr = "";

    child.stdout.on("data", (chunk: Buffer) => {
      stdout += chunk.toString();
    });

    child.stderr.on("data", (chunk: Buffer) => {
      stderr += chunk.toString();
    });

    child.on("close", (code: number) => {
      if (code === 0) {
        try {
          const result = JSON.parse(stdout.trim().split("\n").pop() || "{}");
          resolve(result as EvaluationResult);
        } catch {
          reject(new Error(`Failed to parse evaluation output: ${stdout}`));
        }
      } else {
        reject(new Error(`Python process exited with ${code}: ${stderr}`));
      }
    });

    child.on("error", (err: Error) => {
      reject(err);
    });
  });
}

const worker = new Worker<EvaluationJobData, EvaluationResult>(
  "devascent-evaluations",
  async (job: Job<EvaluationJobData>) => {
    const { sessionId, code, language } = job.data;

    await job.updateProgress({ stage: "sandbox_exec", sessionId });

    const result = await runPythonEvaluation(job.data);

    await job.updateProgress({
      stage: "complete",
      score: result.finalScore,
      sessionId,
    });

    return result;
  },
  {
    connection: { url: REDIS_URL },
    concurrency: 3,
    autorun: true,
  },
);

worker.on("completed", (job) => {
  console.log(`[worker] Job ${job.id} completed`);
});

worker.on("failed", (job, err) => {
  console.error(`[worker] Job ${job?.id} failed:`, err.message);
});

process.on("SIGTERM", async () => {
  console.log("[worker] Shutting down...");
  await worker.close();
  process.exit(0);
});

export { worker };
