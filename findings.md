# Findings — Illegal dumping requests, Los Angeles 2024

Status as of 2025-07-18. Each number points to the CSV in `results/` that reproduces it.

## Key findings
1. **Illegal dumping is the type that gets stuck.** 6,305 of 114,263 illegal-dumping requests (**5.5%**) still had no closed date in July 2025 — **3.2×** the rate for Bulky Item pickups (1.7%). *(type_summary.csv)*
2. **The backlog is "Pending", not slow crews.** Requests that do close are closed fast (median **2.24 days**, 57.6% within 3 days), but the open backlog grew from **901** at the end of the first week of 2024 to **7,587** by late December; **83.9%** of the requests still unresolved in July 2025 sit in *Pending* status. *(type_summary.csv, weekly_illegal_dumping.csv, unresolved_status_illegal_dumping.csv)*
3. **Big gaps between districts.** Council District 3 left **12.4%** of its 2024 requests unresolved vs. **2.6%** in District 2. District 8 generates the most reports (16,512, 14.5% of the city); Districts 8, 6 and 9 together account for **35.1%**. *(district_illegal_dumping.csv)*
4. **Weekend dumping lands on Monday.** Monday receives **22,709** reports (19.9% of the week) vs. 8,857 on Saturday, while Sunday closes only 1,620 — work piles up over the weekend and is cleared Tue–Fri. *(weekday_pattern.csv)*
5. **Phone reports wait longer.** About half of reports still come by phone (51.9%); their median time to close is **2.82 days** vs. **2.06 days** for the mobile app. *(channel_illegal_dumping.csv)*
6. **One cohort stands out.** 12.6% of June 2024 requests were still unresolved, well above May (7.3%) and July (5.3%) — worth checking against operational changes that month. *(monthly_cohort_illegal_dumping.csv)*

## Recommendations (for a sanitation operations manager)
- Add a weekly review of *Pending* illegal-dumping requests older than 14 days, starting with District 3.
- Shift part of the crew capacity toward Monday–Tuesday to absorb the weekend spike.
- Promote the MyLA311 app / self-service for dumping reports; investigate why phone-created requests close ~0.8 days slower.
- Track two KPIs on a dashboard: % unresolved after 14 days (by district) and weekly intake − closures.

## Caveats
- Data comes from a community mirror of the city's open data, not the official portal itself.
- "Pending" semantics are not documented in the dataset; some requests may be resolved without a closed date being recorded.
- District comparisons are not normalized by population or area.
- Requests closed after the 2025-07-18 snapshot are counted as unresolved.
