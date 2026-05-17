"use client";

export interface Scenario {
  id: string;
  number: number;
  title: string;
  subtitle: string;
  clinicalStory: string;
  stressTest: string;
  age: number;
  sex: string;
  accentColor: string;
  badgeColor: string;
  endpoint: "assessment_level0" | "full_assessment";
  payload: Record<string, unknown>;
  expectedFindings: string[];
}

interface ScenarioCardProps {
  scenario: Scenario;
  selected: boolean;
  onSelect: () => void;
}

export default function ScenarioCard({ scenario, selected, onSelect }: ScenarioCardProps) {
  return (
    <button
      onClick={onSelect}
      className={`w-full text-left rounded-2xl border-2 p-5 transition-all hover:shadow-md ${
        selected
          ? `border-${scenario.accentColor}-500 bg-${scenario.accentColor}-50 shadow-md`
          : "border-gray-200 bg-white hover:border-gray-300"
      }`}
    >
      <div className="flex items-start gap-3">
        <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 font-black text-sm ${
          selected ? `bg-${scenario.accentColor}-500 text-white` : "bg-gray-100 text-gray-500"
        }`}>
          {scenario.number}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <span className="font-black text-gray-900 text-sm">{scenario.title}</span>
            <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${scenario.badgeColor}`}>
              {scenario.subtitle}
            </span>
          </div>
          <p className="text-xs text-gray-500 leading-relaxed line-clamp-2">{scenario.clinicalStory}</p>
          <p className="text-xs text-gray-400 mt-1.5 font-medium">
            <span className="text-gray-500">Stress test:</span> {scenario.stressTest}
          </p>
        </div>
      </div>
    </button>
  );
}
