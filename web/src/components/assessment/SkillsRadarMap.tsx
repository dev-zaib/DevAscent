/**
 * SkillsRadarMap — SVG radar chart showing skill dimensions.
 *
 * Animated radar/polar chart with 6-8 skill axes.
 * Color-coded: green (>75), yellow (50-75), red (<50).
 */
interface SkillsRadarMapProps {
  skills: Record<string, number>;
  size?: number;
}

export function SkillsRadarMap({ skills, size = 200 }: SkillsRadarMapProps) {
  const entries = Object.entries(skills);
  const center = size / 2;
  const radius = center - 30;
  const angle = (2 * Math.PI) / Math.max(entries.length, 1);

  if (entries.length === 0) {
    return (
      <div className="flex items-center justify-center text-neutral-600 text-xs" style={{ width: size, height: size }}>
        No skills yet
      </div>
    );
  }

  function getColor(score: number): string {
    if (score >= 75) return "#22c55e";
    if (score >= 50) return "#eab308";
    return "#ef4444";
  }

  const points = entries.map(([_, score], i) => {
    const r = (score / 100) * radius;
    const x = center + r * Math.cos(angle * i - Math.PI / 2);
    const y = center + r * Math.sin(angle * i - Math.PI / 2);
    return `${x},${y}`;
  });

  const maxPoints = entries
    .map((_, i) => {
      const x = center + radius * Math.cos(angle * i - Math.PI / 2);
      const y = center + radius * Math.sin(angle * i - Math.PI / 2);
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      {/* Grid rings */}
      {[0.25, 0.5, 0.75, 1].map((r) => (
        <circle
          key={r}
          cx={center}
          cy={center}
          r={radius * r}
          fill="none"
          stroke="#1f2937"
          strokeWidth={r === 1 ? 1 : 0.5}
        />
      ))}

      {/* Axis lines */}
      {entries.map((_, i) => {
        const x = center + radius * Math.cos(angle * i - Math.PI / 2);
        const y = center + radius * Math.sin(angle * i - Math.PI / 2);
        return (
          <line
            key={i}
            x1={center}
            y1={center}
            x2={x}
            y2={y}
            stroke="#1f2937"
            strokeWidth={0.5}
          />
        );
      })}

      {/* Max outline */}
      <polygon
        points={maxPoints}
        fill="none"
        stroke="#374151"
        strokeWidth={1}
      />

      {/* Data polygon */}
      <polygon
        points={points.join(" ")}
        fill="rgba(34, 197, 94, 0.15)"
        stroke="rgba(34, 197, 94, 0.5)"
        strokeWidth={1.5}
      />

      {/* Data points */}
      {entries.map(([_, score], i) => {
        const r = (score / 100) * radius;
        const x = center + r * Math.cos(angle * i - Math.PI / 2);
        const y = center + r * Math.sin(angle * i - Math.PI / 2);
        return (
          <circle
            key={i}
            cx={x}
            cy={y}
            r={3}
            fill={getColor(score)}
            stroke="#0a0a0a"
            strokeWidth={1}
          />
        );
      })}

      {/* Labels */}
      {entries.map(([name, score], i) => {
        const x =
          center + (radius + 20) * Math.cos(angle * i - Math.PI / 2);
        const y =
          center + (radius + 20) * Math.sin(angle * i - Math.PI / 2);
        return (
          <text
            key={i}
            x={x}
            y={y}
            textAnchor="middle"
            dominantBaseline="middle"
            fill={getColor(score)}
            fontSize={10}
            fontFamily="monospace"
          >
            {name.replace(/_/g, "\n")}
          </text>
        );
      })}
    </svg>
  );
}

/**
 * SkillBarMeter — horizontal bar chart for detailed skill scores.
 */
interface SkillBarMeterProps {
  skills: Record<string, number>;
}

export function SkillBarMeter({ skills }: SkillBarMeterProps) {
  const entries = Object.entries(skills).sort(([, a], [, b]) => b - a);

  function getBarColor(score: number): string {
    if (score >= 75) return "bg-green-500";
    if (score >= 50) return "bg-amber-500";
    return "bg-red-500";
  }

  return (
    <div className="space-y-3">
      {entries.map(([name, score]) => (
        <div key={name}>
          <div className="flex justify-between text-xs mb-1">
            <span className="text-neutral-400 capitalize">
              {name.replace(/_/g, " ")}
            </span>
            <span className="font-mono text-neutral-300">{score}</span>
          </div>
          <div className="w-full bg-neutral-800 rounded-full h-2">
            <div
              className={`h-2 rounded-full transition-all duration-700 ${getBarColor(score)}`}
              style={{ width: `${score}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
