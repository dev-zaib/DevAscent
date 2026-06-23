/**
 * LevelBadge — animated level indicator.
 *
 * Levels: BASELINE → SYSTEM_DESIGNER → TOP_1_PERCENT → ARCHITECT → DISTINGUISHED
 */
interface LevelBadgeProps {
  level: string;
  escalationDepth?: number;
}

const LEVEL_STYLES: Record<string, { color: string; ring: string; symbol: string }> = {
  BASELINE: { color: "#a1a1aa", ring: "ring-zinc-500", symbol: "◈" },
  SYSTEM_DESIGNER: { color: "#22c55e", ring: "ring-green-500", symbol: "◆" },
  TOP_1_PERCENT: { color: "#eab308", ring: "ring-amber-500", symbol: "⬡" },
  ARCHITECT: { color: "#a855f7", ring: "ring-purple-500", symbol: "⬢" },
  DISTINGUISHED: { color: "#3b82f6", ring: "ring-blue-500", symbol: "✧" },
};

export function LevelBadge({ level, escalationDepth = 0 }: LevelBadgeProps) {
  const style = LEVEL_STYLES[level] ?? LEVEL_STYLES.BASELINE;

  return (
    <div className="text-center">
      <div
        className={`inline-flex items-center justify-center w-16 h-16 rounded-full ring-2 ${style.ring} bg-neutral-900/50 mb-2`}
      >
        <span className="text-2xl" style={{ color: style.color }}>
          {style.symbol}
        </span>
      </div>
      <div className="text-sm font-medium" style={{ color: style.color }}>
        {level.replace(/_/g, " ")}
      </div>
      {escalationDepth > 0 && (
        <div className="text-xs text-red-400 mt-1">
          Depth {escalationDepth}
        </div>
      )}
    </div>
  );
}
