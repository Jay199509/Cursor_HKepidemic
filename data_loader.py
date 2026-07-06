"""从 Excel 读取香港各区疫情数据，供大屏 API 使用。"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd

EXCEL_NAME = "香港各区疫情数据_20250322.xlsx"


@lru_cache(maxsize=1)
def get_raw_df() -> pd.DataFrame:
    base = Path(__file__).resolve().parent
    path = base / EXCEL_NAME
    if not path.exists():
        raise FileNotFoundError(f"未找到数据文件: {path}")
    return pd.read_excel(path)


def prepared_frames():
    df = get_raw_df()
    date_col = df.columns[0]
    district_col = df.columns[1]
    daily_new_col = df.columns[2]
    cumulative_col = df.columns[3]
    # 表结构：第 5 列为各区「现存确诊」（与脚本列索引一致）
    active_col = df.columns[4] if len(df.columns) > 4 else None
    risk_col = df.columns[11] if len(df.columns) > 11 else None

    work = df.copy()
    work["_date"] = pd.to_datetime(work[date_col], errors="coerce")
    work = work.dropna(subset=["_date"])
    work["_daily"] = pd.to_numeric(work[daily_new_col], errors="coerce").fillna(0).astype(int)
    work["_cum"] = pd.to_numeric(work[cumulative_col], errors="coerce").fillna(0).astype(int)
    if active_col is not None:
        work["_active"] = pd.to_numeric(work[active_col], errors="coerce").fillna(0).astype(int)
    else:
        work["_active"] = 0
    if risk_col is not None:
        work["_risk"] = work[risk_col].astype(str)
    else:
        work["_risk"] = ""

    daily_hk = (
        work.groupby("_date", as_index=False)
        .agg(daily_new=("_daily", "sum"), cumulative=("_cum", "sum"))
        .sort_values("_date")
    )

    latest_date = work["_date"].max()

    # 各区在最新一日的累计（取该日该区的累计值）
    last_day = work[work["_date"] == latest_date]
    district_cum = (
        last_day.groupby(district_col, as_index=False)["_cum"]
        .max()
        .rename(columns={district_col: "district", "_cum": "cumulative"})
        .sort_values("cumulative", ascending=False)
    )

    # 各区在最新一日的新增
    district_daily = (
        last_day.groupby(district_col, as_index=False)["_daily"]
        .sum()
        .rename(columns={district_col: "district", "_daily": "daily_new"})
        .sort_values("daily_new", ascending=False)
    )

    # 各区在最新一日的现存确诊（按区取该日记录中的最大值，避免重复行）
    district_active = (
        last_day.groupby(district_col, as_index=False)["_active"]
        .max()
        .rename(columns={district_col: "district", "_active": "active"})
        .sort_values("active", ascending=False)
    )

    # 月度新增（全港）
    work["_ym"] = work["_date"].dt.to_period("M").astype(str)
    monthly = (
        work.groupby("_ym", as_index=False)["_daily"]
        .sum()
        .rename(columns={"_ym": "month", "_daily": "new_cases"})
        .sort_values("month")
    )

    # 风险等级：最新日各记录计数
    risk_dist = None
    if risk_col is not None and not last_day.empty:
        risk_dist = (
            last_day.groupby("_risk").size().reset_index(name="count").rename(columns={"_risk": "level"})
        )

    return {
        "daily_hk": daily_hk,
        "latest_date": latest_date,
        "district_cum": district_cum,
        "district_daily": district_daily,
        "district_active": district_active,
        "monthly": monthly,
        "risk_dist": risk_dist,
    }


def overview_stats():
    """核心指标与各图表数据源对齐（趋势终点 / 地图汇总 / 月度末柱 / Top10 首位等）。"""
    ctx = prepared_frames()
    dh = ctx["daily_hk"]
    da = ctx["district_active"]
    dc = ctx["district_cum"]
    monthly = ctx["monthly"]
    rd = ctx["risk_dist"]

    if dh.empty:
        return {}

    last = dh.iloc[-1]
    first = dh.iloc[0]

    active_total = int(da["active"].sum()) if not da.empty else 0
    if not da.empty:
        ar = da.sort_values("active", ascending=False).iloc[0]
        active_top_district = str(ar["district"])
        active_top_value = int(ar["active"])
    else:
        active_top_district = ""
        active_top_value = 0

    if not dc.empty:
        cr = dc.iloc[0]
        cum_top_district = str(cr["district"])
        cum_top_value = int(cr["cumulative"])
    else:
        cum_top_district = ""
        cum_top_value = 0

    if not monthly.empty:
        mr = monthly.iloc[-1]
        latest_month = str(mr["month"])
        latest_month_new = int(mr["new_cases"])
    else:
        latest_month = ""
        latest_month_new = 0

    risk_main_level = ""
    risk_main_pct = 0.0
    if rd is not None and not rd.empty:
        i = int(rd["count"].astype(int).values.argmax())
        row = rd.iloc[i]
        risk_main_level = str(row["level"])
        tot = int(rd["count"].sum())
        risk_main_pct = round(100.0 * int(row["count"]) / tot, 1) if tot else 0.0

    return {
        "date_range": {
            "start": first["_date"].strftime("%Y-%m-%d"),
            "end": last["_date"].strftime("%Y-%m-%d"),
        },
        "latest_date": ctx["latest_date"].strftime("%Y-%m-%d"),
        "latest_daily_new": int(last["daily_new"]),
        "latest_cumulative": int(last["cumulative"]),
        "active_total": active_total,
        "active_top_district": active_top_district,
        "active_top_value": active_top_value,
        "cum_top_district": cum_top_district,
        "cum_top_value": cum_top_value,
        "latest_month": latest_month,
        "latest_month_new": latest_month_new,
        "risk_main_level": risk_main_level,
        "risk_main_pct": risk_main_pct,
    }
