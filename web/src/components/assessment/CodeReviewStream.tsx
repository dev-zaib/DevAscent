/**
 * CodeReviewStream — real-time SSE evaluation stream display.
 *
 * Shows sandbox output, rubric scores as they arrive, and
 * virtualized terminal output for large evaluation logs.
 */
import { useSSE } from "../../hooks/useSSE";

interface CodeReviewStreamProps {
  jobId: string | null;
  submittedCode: string;
  language: string;
}

export function CodeReviewStream({
  jobId,
  submittedCode,
  language,
}: CodeReviewStreamProps) {
  const { connected, progress, rubricEvents, skillsMatrix, complete, error } =
    useSSE(jobId);

  return (
    <div className="h-full flex flex-col font-mono">
      {/* Status bar */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-neutral-800 bg-neutral-950">
        <div className="flex items-center gap-2">
          <div
            className={`w-2 h-2 rounded-full ${
              connected
                ? "bg-green-500"
                : jobId
                  ? "bg-amber-500"
                  : "bg-neutral-600"
            }`}
          />
          <span className="text-xs text-neutral-400">
            {connected
              ? "Connected"
              : jobId
                ? "Connecting..."
                : "Waiting for submission"}
          </span>
        </div>
        <div className="text-xs text-neutral-600">
          {progress?.stage && progress.stage.replace(/_/g, " ")}
        </div>
      </div>

      {/* Submitted code preview */}
      {submittedCode && !jobId && (
        <div className="flex-1 overflow-y-auto p-4">
          <div className="text-xs text-neutral-500 mb-2">
            Submitted code ({language}):
          </div>
          <pre className="text-sm text-neutral-300 bg-neutral-950 rounded p-4 overflow-x-auto">
            <code>{submittedCode}</code>
          </pre>
        </div>
      )}

      {/* Evaluation stream */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {/* Progress message */}
        {progress && (
          <div className="flex items-start gap-2">
            <span className="text-amber-400 text-xs">→</span>
            <span className="text-xs text-neutral-400">{progress.message}</span>
          </div>
        )}

        {/* Rubric scores */}
        {rubricEvents.map((event, i) => (
          <div
            key={i}
            className="p-3 rounded bg-neutral-900/50 border border-neutral-800/50"
          >
            <div className="flex justify-between items-center mb-1">
              <span className="text-xs text-neutral-300 font-medium">
                {event.dimension}
              </span>
              <span className="text-xs font-mono text-amber-400">
                {event.score}/{event.maxScore}
              </span>
            </div>
            <div className="w-full bg-neutral-800 rounded-full h-1.5">
              <div
                className="bg-amber-500 h-1.5 rounded-full transition-all duration-500"
                style={{ width: `${(event.score / event.maxScore) * 100}%` }}
              />
            </div>
            <p className="text-xs text-neutral-500 mt-1.5">{event.feedback}</p>
          </div>
        ))}

        {/* Skills matrix update */}
        {Object.keys(skillsMatrix).length > 0 && (
          <div className="p-3 rounded bg-blue-950/30 border border-blue-900/30">
            <div className="text-xs text-blue-300 font-medium mb-2">
              Updated Skills Matrix
            </div>
            <div className="space-y-1">
              {Object.entries(skillsMatrix).map(([skill, score]) => (
                <div key={skill} className="flex justify-between">
                  <span className="text-xs text-neutral-400">{skill}</span>
                  <span className="text-xs font-mono text-blue-300">
                    {score}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Complete */}
        {complete && (
          <div className="p-4 rounded bg-green-950/30 border border-green-900/30">
            <div className="text-sm text-green-300 font-semibold mb-1">
              Evaluation Complete
            </div>
            <div className="text-2xl font-bold text-green-400 mb-2">
              {complete.finalScore}/100
            </div>
            <div className="text-xs text-green-300/70">{complete.message}</div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="p-3 rounded bg-red-950/30 border border-red-900/30">
            <div className="text-xs text-red-300 font-medium mb-1">
              {error.code}
            </div>
            <div className="text-xs text-red-400">{error.message}</div>
          </div>
        )}
      </div>
    </div>
  );
}
