/** 30-day line chart for a selected provider and rate type (Plotly.js). */

"use client";

import Plot from "react-plotly.js";

import { HistoryPoint } from "@/interfaces/rates";
import { formatRateType } from "@/lib/format";
import styles from "./RateChart.module.css";

interface Props {
  data: HistoryPoint[];
  provider: string;
  rateType: string;
}

export function RateChart({ data, provider, rateType }: Props) {
  if (data.length === 0) {
    return (
      <p className={styles.empty}>
        No history data for {provider} — {formatRateType(rateType)}.
      </p>
    );
  }

  const title = `${provider} — ${formatRateType(rateType)}`;

  return (
    <div className={styles.chart}>
      <Plot
        data={[
          {
            x: data.map((point) => point.effective_date),
            y: data.map((point) => point.rate_value),
            type: "scatter",
            mode: "lines+markers",
            name: "Rate",
            line: { color: "#2563eb", width: 2 },
            marker: { size: 6, color: "#2563eb" },
            hovertemplate: "%{y:.2f}%<br>%{x|%b %d, %Y}<extra></extra>",
          },
        ]}
        layout={{
          title: { text: title, font: { size: 14 } },
          height: 300,
          margin: { t: 40, r: 16, b: 40, l: 48 },
          xaxis: {
            title: "",
            tickformat: "%b %d",
            gridcolor: "#edf0f4",
          },
          yaxis: {
            title: "Rate (%)",
            tickformat: ".2f",
            gridcolor: "#edf0f4",
          },
          paper_bgcolor: "transparent",
          plot_bgcolor: "transparent",
        }}
        config={{ displayModeBar: false, responsive: true }}
        style={{ width: "100%" }}
        useResizeHandler
      />
    </div>
  );
}
