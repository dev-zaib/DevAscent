/**
 * EscalationGauge — shows Go Harder escalation intensity.
 *
 * Depth 0: Normal assessment
 * Depth 1: Scale/latency/data constraints
 * Depth 2: Fault/partition/exhaustion constraints
 * Depth 3: Security/failover/migration constraints
 */
interface EscalationGaugeProps {
  depth: number;
}

const DEPTH_LABELS = ["Normal", "Chaos L1", "Chaos L2", "Maximum Chaos"];

export function EscalationGauge({ depth }: EscalationGaugeProps) {
  return (
    <div>
      <div className="text-xs font-medium text-neutral-500 uppercase tracking-wide mb-2">
        Escalation
      </div>
      <div className="flex gap-1">
        {[0, 1, 2, 3].map((i) => (
          <div
            key={i}
            className={`flex-1 h-2 rounded-full transition-colors duration-500 ${
              i <= depth
                ? i === 3
                  ? "bg-red-500"
                  : i === 2
                    ? "bg-amber-500"
                    : "bg-amber-400/70"
                : "bg-neutral-800"
            }`}
          />
        ))}
      </div>
      <div className="flex justify-between mt-1">
        {DEPTH_LABELS.map((label, i) => (
          <span
            key={i}
            className={`text-[10px] ${
              i <= depth ? "text-neutral-400" : "text-neutral-700"
            }`}
          >
            {label}
          </span>
        ))}
      </div>
    </div>
  );
}
