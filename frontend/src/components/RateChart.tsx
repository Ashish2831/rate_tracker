"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import styles from "./RateChart.module.css";

interface Props {
  data: { effective_date: string; rate_value: number }[];
  provider: string;
  rateType: string;
}

export function RateChart({ data, provider, rateType }: Props) {
  if (data.length === 0) {
    return (
      <p className={styles.empty}>
        No history data for {provider} — {rateType.replace(/_/g, " ")}.
      </p>
    );
  }

  return (
    <div className={styles.chart}>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#edf0f4" />
          <XAxis
            dataKey="effective_date"
            tick={{ fontSize: 11 }}
            tickFormatter={(v) => new Date(v).toLocaleDateString(undefined, { month: "short", day: "numeric" })}
          />
          <YAxis tick={{ fontSize: 11 }} domain={["auto", "auto"]} />
          <Tooltip
            formatter={(value: number) => [`${value.toFixed(2)}%`, "Rate"]}
            labelFormatter={(label) => new Date(label).toLocaleDateString()}
          />
          <Line
            type="monotone"
            dataKey="rate_value"
            stroke="#2563eb"
            strokeWidth={2}
            dot={{ r: 3 }}
            activeDot={{ r: 5 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
