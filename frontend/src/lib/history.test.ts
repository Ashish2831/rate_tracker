/** Unit tests for history chart point mapping. */

import { describe, expect, it } from "vitest";

import { HistoryRate } from "@/interfaces/rates";
import { toHistoryPoints } from "@/lib/history";

const rows: HistoryRate[] = [
  {
    id: 1,
    provider: "Bank of America",
    rate_type: "30yr_fixed_mortgage",
    rate_value: "6.9858",
    effective_date: "2026-02-28",
    ingestion_ts: "2026-02-28T12:00:00Z",
    currency: "USD",
  },
  {
    id: 2,
    provider: "Bank of America",
    rate_type: "30yr_fixed_mortgage",
    rate_value: "7.5597",
    effective_date: "2026-03-01",
    ingestion_ts: "2026-03-01T23:13:45Z",
    currency: "USD",
  },
  {
    id: 3,
    provider: "Bank of America",
    rate_type: "30yr_fixed_mortgage",
    rate_value: null,
    effective_date: "2026-03-02",
    ingestion_ts: "2026-03-02T00:00:00Z",
    currency: "USD",
  },
];

describe("toHistoryPoints", () => {
  it("maps deduped API rows to chart points", () => {
    const points = toHistoryPoints(rows);
    expect(points).toEqual([
      { effective_date: "2026-02-28", rate_value: 6.9858 },
      { effective_date: "2026-03-01", rate_value: 7.5597 },
    ]);
  });

  it("sorts by effective_date ascending", () => {
    const points = toHistoryPoints([rows[1], rows[0]]);
    expect(points.map((p) => p.effective_date)).toEqual(["2026-02-28", "2026-03-01"]);
  });
});
