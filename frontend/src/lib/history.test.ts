/** Unit tests for daily history aggregation (chart data). */

import { describe, expect, it } from "vitest";

import { HistoryRate } from "@/interfaces/rates";
import { aggregateHistoryByDay } from "@/lib/history";

const rows: HistoryRate[] = [
  {
    id: 1,
    provider: "Bank of America",
    rate_type: "30yr_fixed_mortgage",
    rate_value: "6.00",
    effective_date: "2024-09-25",
    ingestion_ts: "2024-09-25T00:00:00Z",
    currency: "USD",
  },
  {
    id: 2,
    provider: "Bank of America",
    rate_type: "30yr_fixed_mortgage",
    rate_value: "8.00",
    effective_date: "2024-09-25",
    ingestion_ts: "2024-09-25T01:00:00Z",
    currency: "USD",
  },
  {
    id: 3,
    provider: "Bank of America",
    rate_type: "30yr_fixed_mortgage",
    rate_value: "7.00",
    effective_date: "2024-09-26",
    ingestion_ts: "2024-09-26T00:00:00Z",
    currency: "USD",
  },
];

describe("aggregateHistoryByDay", () => {
  it("averages multiple snapshots on the same effective_date", () => {
    const points = aggregateHistoryByDay(rows);
    expect(points).toHaveLength(2);
    expect(points[0]).toEqual({ effective_date: "2024-09-25", rate_value: 7 });
    expect(points[1]).toEqual({ effective_date: "2024-09-26", rate_value: 7 });
  });

  it("sorts by date ascending", () => {
    const points = aggregateHistoryByDay([
      rows[2],
      rows[0],
      rows[1],
    ]);
    expect(points.map((p) => p.effective_date)).toEqual(["2024-09-25", "2024-09-26"]);
  });
});
