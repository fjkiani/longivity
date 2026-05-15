"use client";

interface Props {
  chronologicalAge: number;
  phenoAge: number | null;
  tier: string;
}

export default function PhenoAgeGauge({ chronologicalAge, phenoAge, tier }: Props) {
  const delta = phenoAge != null ? phenoAge - chronologicalAge : null;
  const isAccelerated = delta != null && delta > 2;
  const isHealthy = delta != null && delta < -2;

  const color = isAccelerated ? "#ef4444" : isHealthy ? "#16a34a" : "#f59e0b";
  const bgColor = isAccelerated ? "bg-red-50" : isHealthy ? "bg-green-50" : "bg-yellow-50";
  const textColor = isAccelerated ? "text-red-700" : isHealthy ? "text-green-700" : "text-yellow-700";

  // Simple arc gauge using SVG
  const radius = 60;
  const cx = 80;
  const cy = 80;
  const startAngle = -210;
  const endAngle = 30;
  const totalAngle = endAngle - startAngle;

  // Map phenoAge to angle (range: chron-20 to chron+20)
  const minAge = chronologicalAge - 20;
  const maxAge = chronologicalAge + 20;
  const clampedPhenoAge = phenoAge != null ? Math.max(minAge, Math.min(maxAge, phenoAge)) : chronologicalAge;
  const fraction = (clampedPhenoAge - minAge) / (maxAge - minAge);
  const needleAngle = startAngle + fraction * totalAngle;

  function polarToCartesian(cx: number, cy: number, r: number, angleDeg: number) {
    const rad = ((angleDeg - 90) * Math.PI) / 180;
    return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
  }

  function arcPath(cx: number, cy: number, r: number, startDeg: number, endDeg: number) {
    const start = polarToCartesian(cx, cy, r, endDeg);
    const end = polarToCartesian(cx, cy, r, startDeg);
    const largeArc = endDeg - startDeg > 180 ? 1 : 0;
    return `M ${start.x} ${start.y} A ${r} ${r} 0 ${largeArc} 0 ${end.x} ${end.y}`;
  }

  const needle = polarToCartesian(cx, cy, radius - 10, needleAngle);

  return (
    <div className={`rounded-xl border p-4 ${bgColor} border-opacity-50`}>
      <h3 className="text-sm font-semibold text-gray-700 mb-2 text-center">Biological Age</h3>
      <div className="flex flex-col items-center">
        <svg width="160" height="100" viewBox="0 0 160 100">
          {/* Background arc */}
          <path
            d={arcPath(cx, cy, radius, startAngle, endAngle)}
            fill="none"
            stroke="#e5e7eb"
            strokeWidth="12"
            strokeLinecap="round"
          />
          {/* Colored arc up to needle */}
          <path
            d={arcPath(cx, cy, radius, startAngle, needleAngle)}
            fill="none"
            stroke={color}
            strokeWidth="12"
            strokeLinecap="round"
          />
          {/* Needle */}
          <line
            x1={cx}
            y1={cy}
            x2={needle.x}
            y2={needle.y}
            stroke="#374151"
            strokeWidth="2"
            strokeLinecap="round"
          />
          <circle cx={cx} cy={cy} r="4" fill="#374151" />
        </svg>

        <div className="text-center -mt-2">
          {phenoAge != null ? (
            <>
              <div className={`text-3xl font-bold ${textColor}`}>{Math.round(phenoAge)}</div>
              <div className="text-xs text-gray-500">biological age</div>
              <div className={`text-sm font-medium mt-1 ${textColor}`}>
                {delta != null && delta > 0 ? `+${Math.round(delta)}` : Math.round(delta || 0)} yrs vs chronological
              </div>
            </>
          ) : (
            <div className="text-sm text-gray-400">Insufficient data</div>
          )}
          <div className="text-xs text-gray-400 mt-1">Chronological: {chronologicalAge} yrs</div>
        </div>
      </div>
    </div>
  );
}
