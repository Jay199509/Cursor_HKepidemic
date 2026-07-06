"""香港疫情数据可视化大屏 — Flask + ECharts"""

from __future__ import annotations

from pathlib import Path

from flask import Flask, jsonify, render_template, send_file

from data_loader import prepared_frames, overview_stats

app = Flask(__name__)


def _district_active_json():
    ctx = prepared_frames()
    da = ctx["district_active"]
    return {
        "stat_date": ctx["latest_date"].strftime("%Y-%m-%d"),
        "districts": da["district"].astype(str).tolist(),
        "values": da["active"].astype(int).tolist(),
    }


@app.route("/")
def index():
    return render_template("dashboard.html")


@app.route("/api/overview")
def api_overview():
    return jsonify(overview_stats())


@app.route("/api/trend")
def api_trend():
    ctx = prepared_frames()
    dh = ctx["daily_hk"]
    dates = [d.strftime("%Y-%m-%d") for d in dh["_date"]]
    return jsonify(
        {
            "dates": dates,
            "daily_new": dh["daily_new"].astype(int).tolist(),
            "cumulative": dh["cumulative"].astype(int).tolist(),
        }
    )


@app.route("/api/district_cumulative_top")
def api_district_cumulative_top():
    ctx = prepared_frames()
    top = ctx["district_cum"].head(10)
    return jsonify(
        {
            "districts": top["district"].astype(str).tolist(),
            "values": top["cumulative"].astype(int).tolist(),
        }
    )


@app.route("/api/monthly_new")
def api_monthly_new():
    ctx = prepared_frames()
    m = ctx["monthly"]
    return jsonify(
        {
            "months": m["month"].tolist(),
            "values": m["new_cases"].astype(int).tolist(),
        }
    )


@app.route("/api/district_active_distribution")
@app.route("/api/district_active_distribution/")
@app.route("/api/district_active")
def api_district_active_distribution():
    """最新统计日：各地区现存确诊（用于地图热力着色）"""
    return jsonify(_district_active_json())


@app.route("/api/hk_districts_geo")
def api_hk_districts_geo():
    """香港 18 区边界 GeoJSON（与 Excel 区名 properties.name 一致）"""
    path = Path(__file__).resolve().parent / "static" / "geo" / "hk_districts_full.json"
    if not path.is_file():
        return jsonify({"error": "geo file missing", "path": str(path)}), 404
    return send_file(path, mimetype="application/json", max_age=3600)


@app.route("/api/district_daily_latest")
def api_district_daily_latest():
    ctx = prepared_frames()
    d = ctx["district_daily"].head(12)
    return jsonify(
        {
            "districts": d["district"].astype(str).tolist(),
            "values": d["daily_new"].astype(int).tolist(),
        }
    )


@app.route("/api/risk_distribution")
def api_risk_distribution():
    ctx = prepared_frames()
    rd = ctx["risk_dist"]
    if rd is None or rd.empty:
        return jsonify({"levels": [], "values": []})
    return jsonify(
        {
            "levels": rd["level"].astype(str).tolist(),
            "values": rd["count"].astype(int).tolist(),
        }
    )


if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", "5000"))
    # Windows 下 debug 重载会启两个进程，容易造成“一闪连不上”；关闭重载更稳
    print()
    print("=" * 56)
    print("  服务已启动，请在浏览器地址栏输入（不要双击打开 html 文件）：")
    print(f"    http://127.0.0.1:{port}/")
    print("  或本机局域网 IP 访问：http://<你的IP>:%d/" % port)
    print("  按 Ctrl+C 停止服务")
    print("=" * 56)
    print()
    app.run(
        host="0.0.0.0",
        port=port,
        debug=True,
        use_reloader=False,
        threaded=True,
    )
