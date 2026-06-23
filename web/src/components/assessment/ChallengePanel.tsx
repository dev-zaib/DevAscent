/**
 * ChallengePanel — renders assessment challenge with markdown.
 *
 * Displays: title, description, difficulty, target skills,
 * rubric dimensions, and progressive hints.
 */
import { useState } from "react";

interface Challenge {
  title: string;
  description: string;
  difficulty: string;
  target_skills: string[];
  target_level: string;
  rubric?: Record<string, { weight: number; description: string }>;
  hints?: string[];
}

interface ChallengePanelProps {
  challenge: Challenge | null;
  isLoading?: boolean;
}

export function ChallengePanel({ challenge, isLoading }: ChallengePanelProps) {
  const [showHints, setShowHints] = useState(false);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full text-neutral-500">
        Loading challenge...
      </div>
    );
  }

  if (!challenge) {
    return (
      <div className="flex items-center justify-center h-full text-neutral-500">
        No challenge selected
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto px-6 py-8 font-sans">
      <div className="space-y-6">
        {/* Header */}
        <div>
          <div className="flex items-center gap-3 mb-2">
            <span className="text-xs font-mono px-2 py-0.5 rounded border border-neutral-800 text-neutral-400 uppercase">
              {challenge.difficulty}
            </span>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-neutral-900 text-neutral-400 uppercase">
              {challenge.target_level}
            </span>
          </div>
          <h2 className="text-2xl font-semibold text-neutral-100 leading-tight">
            {challenge.title}
          </h2>
        </div>

        {/* Description */}
        <div className="text-neutral-300 leading-relaxed whitespace-pre-wrap">
          {challenge.description}
        </div>

        {/* Target Skills */}
        <div>
          <h3 className="text-sm font-medium text-neutral-400 mb-2 uppercase tracking-wide">
            Target Skills
          </h3>
          <div className="flex flex-wrap gap-2">
            {challenge.target_skills.map((skill) => (
              <span
                key={skill}
                className="text-xs px-2.5 py-1 rounded-full bg-neutral-900 text-neutral-300 border border-neutral-800"
              >
                {skill}
              </span>
            ))}
          </div>
        </div>

        {/* Rubric */}
        {challenge.rubric && (
          <div>
            <h3 className="text-sm font-medium text-neutral-400 mb-2 uppercase tracking-wide">
              Rubric
            </h3>
            <div className="space-y-2">
              {Object.entries(challenge.rubric).map(([name, spec]) => (
                <div
                  key={name}
                  className="flex justify-between items-center py-2 px-3 rounded bg-neutral-900/50 border border-neutral-800/50"
                >
                  <div>
                    <span className="text-sm text-neutral-200">{name}</span>
                    <p className="text-xs text-neutral-500 mt-0.5">
                      {spec.description}
                    </p>
                  </div>
                  <span className="text-xs font-mono text-neutral-400 ml-4">
                    {spec.weight}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Hints */}
        {challenge.hints && challenge.hints.length > 0 && (
          <div>
            <button
              onClick={() => setShowHints(!showHints)}
              className="text-sm text-neutral-400 hover:text-neutral-200 transition-colors"
            >
              {showHints ? "Hide" : "Show"} Hints ({challenge.hints.length})
            </button>
            {showHints && (
              <div className="mt-2 space-y-2">
                {challenge.hints.map((hint, i) => (
                  <div
                    key={i}
                    className="p-3 rounded bg-amber-950/30 border border-amber-900/30 text-sm text-amber-200/80"
                  >
                    {hint}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
