import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import font_manager

# 优先选择系统中真实存在的中文字体，避免中文变方块/乱码
preferred_fonts = [
    "Microsoft YaHei",  # Windows 常见
    "SimHei",
    "SimSun",
    "NSimSun",
    "PingFang SC",
    "Noto Sans CJK SC",
    "Source Han Sans SC",
    "Arial Unicode MS",
]
available = {f.name for f in font_manager.fontManager.ttflist}
chosen = next((f for f in preferred_fonts if f in available), "DejaVu Sans")
plt.rcParams["font.sans-serif"] = [chosen]
plt.rcParams["axes.unicode_minus"] = False

# 读取 Excel
df = pd.read_excel("香港各区疫情数据_20250322.xlsx")

# 该表的列名在某些 Windows 终端会显示乱码，这里用“列位置”来稳妥取数：
# 0: 日期, 1: 地区, 2: 每日新增确诊, 3: 累计确诊
date_col = df.columns[0]
daily_new_col = df.columns[2]
cumulative_col = df.columns[3]

# 按“日期”汇总全港
daily = (
    df[[date_col, daily_new_col, cumulative_col]]
    .groupby(date_col, as_index=False)
    .sum(numeric_only=True)
    .rename(
        columns={
            date_col: "日期",
            daily_new_col: "每日新增确诊",
            cumulative_col: "累计确诊",
        }
    )
)

# 日期列转 datetime，横坐标才能正确做稀疏刻度
daily["日期"] = pd.to_datetime(daily["日期"], errors="coerce")
daily = daily.dropna(subset=["日期"]).sort_values("日期")

print(daily.head(20).to_string(index=False))

# 折线图呈现
fig, ax1 = plt.subplots(figsize=(13, 6))

# 左轴：每日新增（更能体现波动）
ax1.plot(
    daily["日期"],
    daily["每日新增确诊"],
    label="每日新增确诊",
    linewidth=2,
    color="#1f77b4",
)
ax1.set_xlabel("日期")
ax1.set_ylabel("每日新增确诊")
ax1.grid(True, linestyle="--", alpha=0.35)

# 右轴：累计（数量级大，单独轴不压扁波动）
ax2 = ax1.twinx()
ax2.plot(
    daily["日期"],
    daily["累计确诊"],
    label="累计确诊",
    linewidth=2,
    color="#ff7f0e",
    alpha=0.9,
)
ax2.set_ylabel("累计确诊")

# 横坐标：按“月”显示为 YYYY-MM（如 2022-01），避免过密
ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
for label in ax1.get_xticklabels():
    label.set_rotation(30)
    label.set_ha("right")

fig.suptitle("确诊病例数趋势（每日新增 vs 累计）")

# 合并两条线的图例
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")

plt.tight_layout()
plt.savefig("confirmed_trends.png", dpi=150)
plt.show()