"""LA 311 Sanitation Requests 2024 — reproducible analysis.

Usage:  python run_analysis.py --data 2024.parquet
Needs:  pip install duckdb pandas matplotlib
Writes: results/*.csv (one per query in queries.sql), charts/*.png, findings.json
"""
import argparse, json, re
from pathlib import Path

import duckdb
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

HERE = Path(__file__).parent
BLUE, ORANGE, GREY, INK, MUTED = "#2a78d6", "#eb6834", "#b9c3cf", "#0b0b0b", "#52514e"
SOURCE = "Source: MyLA311 Service Requests 2024 (City of Los Angeles), Hack for LA mirror; status as of {snap}"


def load_queries(path):
    text = path.read_text(encoding="utf-8")
    parts = re.split(r"^-- name:\s*(\w+)\s*$", text, flags=re.M)
    return {parts[i]: parts[i + 1].strip() for i in range(1, len(parts), 2)}


def style(ax, title, subtitle=None):
    ax.set_title(title, loc="left", fontsize=12, fontweight="bold", color=INK, pad=18 if subtitle else 8)
    if subtitle:
        ax.text(0, 1.02, subtitle, transform=ax.transAxes, fontsize=9, color=MUTED)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#cfcfcf")
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.grid(axis="y", color="#ececec", linewidth=0.8)
    ax.set_axisbelow(True)


def footer(fig, snap):
    fig.text(0.01, 0.005, SOURCE.format(snap=snap), fontsize=7.5, color=MUTED)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="2024.parquet")
    args = ap.parse_args()

    (HERE / "results").mkdir(exist_ok=True)
    (HERE / "charts").mkdir(exist_ok=True)
    con = duckdb.connect()
    con.execute(f"CREATE VIEW raw AS SELECT * FROM read_parquet('{Path(args.data).as_posix()}')")

    res = {}
    for name, sql in load_queries(HERE / "queries.sql").items():
        body = "\n".join(l for l in sql.splitlines() if not l.strip().startswith("--")).strip()
        if body.upper().startswith("CREATE"):
            con.execute(sql)
            continue
        df = con.execute(sql).df()
        df.to_csv(HERE / "results" / f"{name}.csv", index=False)
        res[name] = df
        print(f"{name}: {len(df)} rows")

    dq = res["data_quality"].iloc[0]
    snap = str(dq["snapshot_max_updated"])[:10]

    # 1) Weekly intake vs closed + backlog (two panels, one shared x — no dual axis)
    wk = res["weekly_illegal_dumping"]
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(10, 6.2), sharex=True, gridspec_kw={"height_ratios": [3, 2]})
    a1.plot(wk.week_start, wk.intake, color=BLUE, lw=2, label="Requests created")
    a1.plot(wk.week_start, wk.closed, color=ORANGE, lw=2, label="Requests closed")
    style(a1, "Illegal dumping in Los Angeles, 2024: weekly intake vs. closures",
          "LASAN 'Illegal Dumping Pickup' requests, full Mon–Sun weeks")
    a1.legend(frameon=False, fontsize=9, loc="upper left")
    a2.plot(wk.week_start, wk.open_backlog_at_week_end, color=BLUE, lw=2)
    a2.fill_between(wk.week_start, wk.open_backlog_at_week_end, color=BLUE, alpha=0.12)
    style(a2, "Open backlog at the end of each week")
    a2.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
    fig.tight_layout(rect=(0, 0.03, 1, 1)); footer(fig, snap)
    fig.savefig(HERE / "charts" / "weekly_intake_closed_backlog.png", dpi=160); plt.close(fig)

    # 2) Unresolved share by council district (sorted, highlight the max)
    dist = res["district_illegal_dumping"].sort_values("pct_unresolved")
    fig, ax = plt.subplots(figsize=(8, 5.6))
    colors = [ORANGE if v == dist.pct_unresolved.max() else BLUE for v in dist.pct_unresolved]
    ax.barh([f"CD {int(c)}" for c in dist.council_district], dist.pct_unresolved, color=colors, height=0.66)
    for y, (v, n) in enumerate(zip(dist.pct_unresolved, dist.unresolved)):
        ax.text(v + 0.15, y, f"{v:.1f}%  ({n:,})", va="center", fontsize=8.5, color=INK)
    style(ax, "Share of 2024 illegal-dumping requests still unresolved",
          f"By City Council District, status as of {snap}")
    ax.grid(axis="y", visible=False); ax.grid(axis="x", color="#ececec")
    ax.set_xlabel("% of the district's 2024 requests with no closed date", color=MUTED, fontsize=9)
    fig.tight_layout(rect=(0, 0.03, 1, 1)); footer(fig, snap)
    fig.savefig(HERE / "charts" / "district_unresolved.png", dpi=160); plt.close(fig)

    # 3) Weekday: created vs closed
    wd = res["weekday_pattern"]
    fig, ax = plt.subplots(figsize=(8, 4.4))
    x = range(len(wd)); w = 0.38
    ax.bar([i - w / 2 - 0.01 for i in x], wd.created, w, color=BLUE, label="Created")
    ax.bar([i + w / 2 + 0.01 for i in x], wd.closed, w, color=ORANGE, label="Closed")
    ax.set_xticks(list(x), wd.day)
    style(ax, "Reports peak on Monday; closures happen Tue–Fri",
          "Illegal dumping requests by day of week, 2024")
    ax.legend(frameon=False, fontsize=9)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v/1000:.0f}k"))
    fig.tight_layout(rect=(0, 0.03, 1, 1)); footer(fig, snap)
    fig.savefig(HERE / "charts" / "weekday_pattern.png", dpi=160); plt.close(fig)

    # findings.json — numbers quoted in the CV / portfolio, each traceable to a results CSV
    ts = res["type_summary"].set_index("RequestType")
    idp, bulky = ts.loc["Illegal Dumping Pickup"], ts.loc["Bulky Items"]
    d_all = res["district_illegal_dumping"]
    top3 = d_all.nlargest(3, "requests")
    worst = d_all.loc[d_all.pct_unresolved.idxmax()]; best = d_all.loc[d_all.pct_unresolved.idxmin()]
    ch = res["channel_illegal_dumping"].set_index("RequestSource")
    wdi = wd.set_index("day")
    coh = res["monthly_cohort_illegal_dumping"]; jun = coh.loc[coh.pct_unresolved.idxmax()]
    f = {
        "snapshot": snap,
        "rows_total": int(dq.rows_total), "rows_in_scope": int(dq.rows_in_scope),
        "duplicate_sr_numbers": int(dq.duplicate_sr_numbers), "closed_before_created": int(dq.closed_before_created),
        "closed_status_without_date": int(dq.closed_status_without_date),
        "idp_requests": int(idp.requests), "idp_pct_of_scope": float(idp.pct_of_scope),
        "idp_median_days": float(idp.median_days_closed), "idp_pct_within_3d": float(idp.pct_closed_within_3d),
        "idp_unresolved": int(idp.unresolved_at_snapshot), "idp_pct_unresolved": float(idp.pct_unresolved),
        "bulky_requests": int(bulky.requests), "bulky_pct_unresolved": float(bulky.pct_unresolved),
        "unresolved_ratio_idp_vs_bulky": round(float(idp.pct_unresolved) / float(bulky.pct_unresolved), 1),
        "top_district": int(top3.iloc[0].council_district), "top_district_requests": int(top3.iloc[0].requests),
        "top_district_pct": float(top3.iloc[0].pct_of_citywide),
        "top3_districts": [int(c) for c in top3.council_district], "top3_pct": round(float(top3.pct_of_citywide.sum()), 1),
        "worst_district": int(worst.council_district), "worst_district_pct_unresolved": float(worst.pct_unresolved),
        "best_district": int(best.council_district), "best_district_pct_unresolved": float(best.pct_unresolved),
        "monday_created": int(wdi.loc["Mon", "created"]), "monday_pct": float(wdi.loc["Mon", "pct_created"]),
        "saturday_created": int(wdi.loc["Sat", "created"]), "sunday_closed": int(wdi.loc["Sun", "closed"]),
        "call_median_days": float(ch.loc["Call", "median_days_closed"]), "app_median_days": float(ch.loc["Mobile App", "median_days_closed"]),
        "call_pct_requests": float(ch.loc["Call", "pct_of_requests"]),
        "worst_cohort_month": int(jun.month), "worst_cohort_pct_unresolved": float(jun.pct_unresolved),
        "weekly_intake_max": int(wk.intake.max()), "weekly_intake_min": int(wk.intake.min()),
        "backlog_start": int(wk.open_backlog_at_week_end.iloc[0]), "backlog_end": int(wk.open_backlog_at_week_end.iloc[-1]),
        "unresolved_pending": int(res["unresolved_status_illegal_dumping"].set_index("Status").loc["Pending", "unresolved"]),
        "unresolved_pending_pct": float(res["unresolved_status_illegal_dumping"].set_index("Status").loc["Pending", "pct_of_unresolved"]),
    }
    (HERE / "findings.json").write_text(json.dumps(f, indent=2), encoding="utf-8")
    print(json.dumps(f, indent=2))


if __name__ == "__main__":
    main()
