/** 30-day line chart for a selected provider and rate type (Plotly.js). */

"use client";

import Plot from "react-plotly.js";

import { EmptyState } from "@/components/EmptyState";
import { HistoryPoint } from "@/interfaces/rates";
import { formatRateType } from "@/lib/format";
import styles from "./RateChart.module.css";

interface Props {
  data: HistoryPoint[];
  provider: string;
  rateType: string;
}

const CHART_COLOR = "#0f766e";
const CHART_FILL = "rgba(15, 118, 110, 0.08)";

export function RateChart({ data, provider, rateType }: Props) {
  if (data.length === 0) {
    return (
      <EmptyState
        icon="chart"
        title="No history available"
        description={
          <>
            No data for <strong>{provider || "this provider"}</strong> —{" "}
            {formatRateType(rateType || "selected rate type")}. Try another combination or run{" "}
            <code>make seed</code>.
          </>
        }
      />
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
            line: { color: CHART_COLOR, width: 2.5, shape: "linear" },
            marker: { size: 7, color: CHART_COLOR, line: { color: "#fff", width: 1.5 } },
            fill: "tozeroy",
            fillcolor: CHART_FILL,
            hovertemplate: "<b>%{y:.2f}%</b><br>%{x|%b %d, %Y}<extra></extra>",
          },
        ]}
        layout={{
          title: { text: title, font: { size: 13, color: "#64748b", family: "DM Sans, sans-serif" } },
          height: 320,
          margin: { t: 44, r: 20, b: 48, l: 52 },
          xaxis: {
            title: "",
            tickformat: "%b %d",
            dtick: 86400000 * 3,
            gridcolor: "#f1f5f9",
            linecolor: "#e2e8f0",
            tickfont: { size: 11, color: "#94a3b8" },
          },
          yaxis: {
            title: { text: "Rate (%)", font: { size: 11, color: "#94a3b8" } },
            tickformat: ".2f",
            gridcolor: "#f1f5f9",
            linecolor: "#e2e8f0",
            tickfont: { size: 11, color: "#94a3b8" },
          },
          paper_bgcolor: "transparent",
          plot_bgcolor: "transparent",
          hoverlabel: {
            bgcolor: "#0f172a",
            bordercolor: "#0f172a",
            font: { color: "#f8fafc", size: 12 },
          },
        }}
        config={{ displayModeBar: false, responsive: true }}
        style={{ width: "100%" }}
        useResizeHandler
      />
    </div>
  );
}
