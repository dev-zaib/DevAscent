/**
 * SubmissionHistory — virtualized list of past assessment attempts.
 */
interface EvaluationEntry {
  challenge_id: string;
  score: number;
  rubric_breakdown?: Record<string, number>;
  ai_feedback?: string;
  timestamp: string;
}

interface SubmissionHistoryProps {
  history: EvaluationEntry[];
}

export function SubmissionHistory({ history }: SubmissionHistoryProps) {
  if (history.length === 0) {
    return (
      <div className="text-xs text-neutral-600">
        No submissions yet
      </div>
    );
  }

  return (
    <div className="space-y-2 max-h-[200px] overflow-y-auto">
      {history.map((entry, i) => (
        <div
          key={i}
          className="p-2 rounded bg-neutral-900/30 border border-neutral-800/50"
        >
          <div className="flex justify-between items-center">
            <span className="text-xs text-neutral-400 truncate max-w-[200px]">
              {entry.challenge_id}
            </span>
            <span className="text-xs font-mono font-medium text-amber-400">
              {entry.score}
            </span>
          </div>
          <div className="text-[10px] text-neutral-600 mt-0.5">
            {new Date(entry.timestamp).toLocaleDateString()}
          </div>
        </div>
      ))}
    </div>
  );
}
