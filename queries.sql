-- LA 311 Sanitation Requests 2024 — DuckDB SQL
-- Source: MyLA311 Service Request Data 2024 (City of Los Angeles open data),
--         mirrored by Hack for LA at huggingface.co/datasets/311-data/2024 (file 2024.parquet).
-- Run with: python run_analysis.py --data 2024.parquet   (creates view `raw` over the parquet file)
-- Every query below is executed by run_analysis.py and saved to results/<name>.csv

-- name: base_view
-- Scope: LA Sanitation (LASAN) waste-collection requests created in 2024.
CREATE OR REPLACE VIEW sr AS
SELECT
    SRNumber, RequestType, Status, RequestSource, CD,
    CreatedDate, ClosedDate,
    date_diff('second', CreatedDate, ClosedDate) / 86400.0 AS days_to_close
FROM raw
WHERE Owner = 'LASAN'
  AND RequestType IN ('Bulky Items', 'Illegal Dumping Pickup',
                      'Metal/Household Appliances', 'Electronic Waste');

-- name: data_quality
SELECT
    (SELECT count(*) FROM raw)                                              AS rows_total,
    (SELECT max(UpdatedDate) FROM raw)                                      AS snapshot_max_updated,
    count(*)                                                                AS rows_in_scope,
    count(*) - count(DISTINCT SRNumber)                                     AS duplicate_sr_numbers,
    count(*) FILTER (WHERE ClosedDate < CreatedDate)                        AS closed_before_created,
    count(*) FILTER (WHERE Status = 'Closed' AND ClosedDate IS NULL)        AS closed_status_without_date,
    count(*) FILTER (WHERE ClosedDate IS NULL)                              AS no_closed_date
FROM sr;

-- name: type_summary
-- Volume, service time and share still unresolved at the snapshot, by request type.
SELECT
    RequestType,
    count(*)                                                                AS requests,
    round(100.0 * count(*) / sum(count(*)) OVER (), 1)                      AS pct_of_scope,
    round(median(days_to_close) FILTER (WHERE Status = 'Closed'), 2)        AS median_days_closed,
    round(quantile_cont(days_to_close, 0.9) FILTER (WHERE Status = 'Closed'), 1) AS p90_days_closed,
    round(100.0 * avg(CASE WHEN days_to_close <= 3 THEN 1 ELSE 0 END)
          FILTER (WHERE Status = 'Closed'), 1)                              AS pct_closed_within_3d,
    count(*) FILTER (WHERE ClosedDate IS NULL)                              AS unresolved_at_snapshot,
    round(100.0 * count(*) FILTER (WHERE ClosedDate IS NULL) / count(*), 1) AS pct_unresolved
FROM sr
GROUP BY RequestType
ORDER BY requests DESC;

-- name: weekly_illegal_dumping
-- Weekly intake, closures and open backlog (end of Sunday) for Illegal Dumping Pickup.
-- Full Monday–Sunday weeks of 2024 only (2024-01-01 is a Monday; last full week starts 2024-12-23).
WITH d AS (SELECT * FROM sr WHERE RequestType = 'Illegal Dumping Pickup'),
weeks AS (
    SELECT ws::DATE AS week_start, (ws + INTERVAL 7 DAY) AS week_end
    FROM range(TIMESTAMP '2024-01-01', TIMESTAMP '2024-12-30', INTERVAL 7 DAY) t(ws)
)
SELECT
    w.week_start,
    (SELECT count(*) FROM d WHERE d.CreatedDate >= w.week_end - INTERVAL 7 DAY AND d.CreatedDate < w.week_end) AS intake,
    (SELECT count(*) FROM d WHERE d.ClosedDate  >= w.week_end - INTERVAL 7 DAY AND d.ClosedDate  < w.week_end) AS closed,
    (SELECT count(*) FROM d WHERE d.CreatedDate < w.week_end
                              AND (d.ClosedDate IS NULL OR d.ClosedDate >= w.week_end))                       AS open_backlog_at_week_end
FROM weeks w
ORDER BY w.week_start;

-- name: weekday_pattern
-- When illegal dumping is reported vs when it is closed.
WITH c AS (
    SELECT isodow(CreatedDate) AS dow, count(*) AS created
    FROM sr WHERE RequestType = 'Illegal Dumping Pickup' GROUP BY 1),
k AS (
    SELECT isodow(ClosedDate) AS dow, count(*) AS closed
    FROM sr WHERE RequestType = 'Illegal Dumping Pickup' AND Status = 'Closed' AND ClosedDate IS NOT NULL GROUP BY 1)
SELECT c.dow,
       ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][c.dow] AS day,
       c.created, k.closed,
       round(100.0 * c.created / sum(c.created) OVER (), 1) AS pct_created
FROM c JOIN k USING (dow)
ORDER BY c.dow;

-- name: district_illegal_dumping
-- Illegal dumping by City Council District: volume and share still unresolved at the snapshot.
SELECT
    CD AS council_district,
    count(*)                                                                AS requests,
    round(100.0 * count(*) / sum(count(*)) OVER (), 1)                      AS pct_of_citywide,
    count(*) FILTER (WHERE ClosedDate IS NULL)                              AS unresolved,
    round(100.0 * count(*) FILTER (WHERE ClosedDate IS NULL) / count(*), 1) AS pct_unresolved,
    round(median(days_to_close) FILTER (WHERE Status = 'Closed'), 2)        AS median_days_closed
FROM sr
WHERE RequestType = 'Illegal Dumping Pickup' AND CD IS NOT NULL
GROUP BY CD
ORDER BY requests DESC;

-- name: channel_illegal_dumping
-- Does the reporting channel change how fast illegal dumping is closed?
SELECT
    RequestSource,
    count(*)                                                                AS requests,
    -- denominator = ALL illegal-dumping requests (not only the channels kept by HAVING)
    round(100.0 * count(*) / (SELECT count(*) FROM sr WHERE RequestType = 'Illegal Dumping Pickup'), 1) AS pct_of_requests,
    round(median(days_to_close) FILTER (WHERE Status = 'Closed'), 2)        AS median_days_closed,
    round(100.0 * avg(CASE WHEN days_to_close <= 3 THEN 1 ELSE 0 END)
          FILTER (WHERE Status = 'Closed'), 1)                              AS pct_closed_within_3d
FROM sr
WHERE RequestType = 'Illegal Dumping Pickup'
GROUP BY RequestSource
HAVING count(*) >= 1000
ORDER BY requests DESC;

-- name: monthly_cohort_illegal_dumping
-- Share of each month's requests still unresolved at the snapshot (cohort view).
SELECT
    month(CreatedDate)                                                      AS month,
    count(*)                                                                AS requests,
    count(*) FILTER (WHERE ClosedDate IS NULL)                              AS unresolved,
    round(100.0 * count(*) FILTER (WHERE ClosedDate IS NULL) / count(*), 1) AS pct_unresolved
FROM sr
WHERE RequestType = 'Illegal Dumping Pickup'
GROUP BY 1
ORDER BY 1;

-- name: unresolved_status_illegal_dumping
-- What state are the still-unresolved illegal-dumping requests in?
SELECT Status, count(*) AS unresolved,
       round(100.0 * count(*) / sum(count(*)) OVER (), 1) AS pct_of_unresolved
FROM sr
WHERE RequestType = 'Illegal Dumping Pickup' AND ClosedDate IS NULL
GROUP BY Status
ORDER BY unresolved DESC;
