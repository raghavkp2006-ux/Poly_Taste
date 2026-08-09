import { fontFamily } from "../../tokens"
import { RingChart } from "../charts/ring-chart"
import { Ring } from "../charts/ring"
import { RingCenter } from "../charts/ring-center"

export interface ConvergenceData {
  label: string
  value: number
  maxValue: number
  color?: string
}

export function ConvergenceHalo({
  score,
  data,
}: {
  score?: number
  data?: ConvergenceData[]
}) {
  // If no data is provided (e.g. Hero section), use default/mock data
  const chartData = data || [
    { label: "Music", value: 85, maxValue: 100 },
    { label: "Anime", value: 60, maxValue: 100 },
    { label: "Food", value: 35, maxValue: 100 },
  ]

  return (
    <div
      className="relative flex flex-col items-center gap-6 py-8 w-full"
      aria-label="Taste Convergence — where music, anime, and food intersect"
    >
      {/* Label */}
      <div className="text-center space-y-1">
        <p
          className="text-[10px] uppercase tracking-[0.2em] text-[#71717A] dark:text-[#A1A1AA] transition-colors duration-150 ease-out"
          style={{ fontFamily: fontFamily.mono }}
        >
          Convergence
        </p>
        <p
          className="text-sm text-[#71717A] dark:text-[#A1A1AA] transition-colors duration-150 ease-out"
          style={{ fontFamily: fontFamily.body }}
        >
          Where your signals unite.
        </p>
      </div>

      {/* Ring Chart Diagram */}
      <div className="relative flex justify-center w-full max-w-lg mx-auto h-[240px]">
        <RingChart data={chartData} size={240}>
          {chartData.map((item, index) => (
            <Ring key={item.label} index={index} />
          ))}
          <RingCenter
            defaultLabel="Convergence"
            formatValue={() => (score !== undefined ? `${Math.round(score)}` : "...")}
          />
        </RingChart>
      </div>

      {/* Domain legend */}
      <div
        className="flex items-center gap-5 text-[10px] uppercase tracking-widest mt-2"
        style={{ fontFamily: fontFamily.mono }}
      >
        <LegendItem color="var(--chart-1)" label="Music" />
        <LegendItem color="var(--chart-2)" label="Anime" />
        <LegendItem color="var(--chart-3)" label="Food" />
      </div>
    </div>
  )
}

function LegendItem({ color, label }: { color: string; label: string }) {
  return (
    <div className="flex items-center gap-1.5">
      <div
        className="w-2 h-2 rounded-full"
        style={{ backgroundColor: color }}
      />
      <span className="text-[#71717A] dark:text-[#A1A1AA] transition-colors duration-150 ease-out">{label}</span>
    </div>
  )
}
