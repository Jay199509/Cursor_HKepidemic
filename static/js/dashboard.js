const commonText = { color: '#b8c8d8' };
const axisLine = { lineStyle: { color: 'rgba(100,140,180,0.45)' } };
const splitLine = { lineStyle: { color: 'rgba(60,90,120,0.25)' } };

async function loadJson(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(url + ' ' + response.status);
  return response.json();
}

/** 地图 GeoJSON：优先走 Flask，失败则直连静态文件和外部数据源 */
async function loadHkGeoJson() {
  const urls = [
    '/api/hk_districts_geo',
    '/static/geo/hk_districts_full.json',
    'https://geo.datav.aliyun.com/areas_v3/bound/810000_full.json',
  ];
  let lastErr;
  for (let i = 0; i < urls.length; i++) {
    try {
      return await loadJson(urls[i]);
    } catch (e) {
      lastErr = e;
    }
  }
  throw lastErr;
}

function setText(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
}

function setOverview(o) {
  if (!o.date_range) return;
  setText('kpi-cumulative', o.latest_cumulative != null ? Number(o.latest_cumulative).toLocaleString() : '—');
  setText('kpi-daily-new', o.latest_daily_new != null ? Number(o.latest_daily_new).toLocaleString() : '—');
  setText('kpi-active-total', o.active_total != null ? Number(o.active_total).toLocaleString() : '—');
  setText('kpi-active-top-district', o.active_top_district || '—');
  setText('kpi-active-top-value', o.active_top_value != null ? Number(o.active_top_value).toLocaleString() : '—');
  setText('kpi-month-label', o.latest_month ? '月份 ' + o.latest_month : '—');
  setText('kpi-month-new', o.latest_month_new != null ? Number(o.latest_month_new).toLocaleString() : '—');
  setText('kpi-cum-top-district', o.cum_top_district || '—');
  setText('kpi-cum-top-value', o.cum_top_value != null ? Number(o.cum_top_value).toLocaleString() : '—');
  setText('kpi-latest-date', o.latest_date || '—');
  setText('kpi-range-text', o.date_range.start + ' ~ ' + o.date_range.end);

  const riskEl = document.getElementById('kpi-risk-text');
  const riskLine = document.getElementById('kpi-risk-line');
  if (riskEl && o.risk_main_level) {
    riskEl.textContent = o.risk_main_level + '，' + (o.risk_main_pct != null ? o.risk_main_pct : '—') + '%';
    if (riskLine) riskLine.style.display = '';
  } else {
    if (riskEl) riskEl.textContent = '—';
    if (riskLine) riskLine.style.display = 'none';
  }
}

function tickDashClock() {
  const el = document.getElementById('dash-clock');
  if (!el) return;
  el.textContent = new Date().toLocaleString('zh-CN', { hour12: false });
}
setInterval(tickDashClock, 1000);
tickDashClock();

function initTrend(el, data) {
  const chart = echarts.init(el, null, { renderer: 'canvas' });
  chart.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
    legend: { data: ['每日新增', '累计确诊'], textStyle: commonText, top: 10 },
    grid: { left: 48, right: 56, top: 52, bottom: 28, containLabel: true },
    xAxis: {
      type: 'category',
      data: data.dates,
      axisLabel: { color: '#8aa4bc', rotate: 28, fontSize: 10 },
      axisLine,
    },
    yAxis: [
      {
        type: 'value',
        name: '每日新增',
        nameTextStyle: { color: '#5cc8ff', fontSize: 11 },
        axisLabel: { color: '#8aa4bc' },
        axisLine,
        splitLine,
      },
      {
        type: 'value',
        name: '累计确诊',
        nameTextStyle: { color: '#ffb347', fontSize: 11 },
        axisLabel: { color: '#8aa4bc' },
        axisLine,
        splitLine: { show: false },
      },
    ],
    series: [
      {
        name: '每日新增',
        type: 'line',
        smooth: true,
        symbol: 'none',
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(0, 200, 255, 0.45)' },
            { offset: 1, color: 'rgba(0, 80, 120, 0.05)' },
          ]),
        },
        lineStyle: { width: 2, color: '#00c8ff' },
        data: data.daily_new,
        yAxisIndex: 0,
      },
      {
        name: '累计确诊',
        type: 'line',
        smooth: true,
        symbol: 'none',
        lineStyle: { width: 2, color: '#ff9f43' },
        data: data.cumulative,
        yAxisIndex: 1,
      },
    ],
  });
  window.addEventListener('resize', () => chart.resize());
  return chart;
}

function initBarH(el, data) {
  const chart = echarts.init(el);
  chart.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 8, right: 24, top: 14, bottom: 10, containLabel: true },
    xAxis: { type: 'value', axisLabel: { color: '#8aa4bc' }, axisLine, splitLine },
    yAxis: {
      type: 'category',
      data: data.districts,
      axisLabel: { color: '#8aa4bc', fontSize: 11 },
      axisLine,
    },
    series: [
      {
        type: 'bar',
        data: data.values,
        itemStyle: {
          borderRadius: [0, 4, 4, 0],
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#0066aa' },
            { offset: 1, color: '#00c8f0' },
          ]),
        },
      },
    ],
  });
  window.addEventListener('resize', () => chart.resize());
  return chart;
}

function initBarV(el, data) {
  const chart = echarts.init(el);
  chart.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis' },
    grid: { left: 40, right: 16, top: 14, bottom: 48, containLabel: true },
    xAxis: {
      type: 'category',
      data: data.months,
      axisLabel: { color: '#8aa4bc', rotate: 32, fontSize: 10 },
      axisLine,
    },
    yAxis: { type: 'value', axisLabel: { color: '#8aa4bc' }, axisLine, splitLine },
    series: [
      {
        type: 'bar',
        data: data.values,
        itemStyle: {
          borderRadius: [4, 4, 0, 0],
          color: new echarts.graphic.LinearGradient(0, 1, 0, 0, [
            { offset: 0, color: 'rgba(0,100,160,0.3)' },
            { offset: 1, color: '#2ec7c9' },
          ]),
        },
      },
    ],
  });
  window.addEventListener('resize', () => chart.resize());
  return chart;
}

function initBarDistrict(el, data) {
  const chart = echarts.init(el);
  chart.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis' },
    grid: { left: 36, right: 12, top: 14, bottom: 72, containLabel: true },
    xAxis: {
      type: 'category',
      data: data.districts,
      axisLabel: { color: '#8aa4bc', rotate: 40, fontSize: 10 },
      axisLine,
    },
    yAxis: { type: 'value', name: '新增', nameTextStyle: { color: '#7a9ab8' }, axisLabel: { color: '#8aa4bc' }, axisLine, splitLine },
    series: [
      {
        type: 'bar',
        data: data.values,
        itemStyle: {
          borderRadius: [4, 4, 0, 0],
          color: '#4ecb73',
        },
      },
    ],
  });
  window.addEventListener('resize', () => chart.resize());
  return chart;
}

/** 各地区现存确诊：ECharts 地图 + 连续型 visualMap，用于分区热力着色 */
function initActiveMapHeat(el, geoJson, data) {
  echarts.registerMap('HK_18', geoJson);

  const values = data.values && data.values.length ? data.values : [0];
  const vmax = Math.max.apply(
    null,
    values.map(function (v) {
      return Number(v);
    })
  );

  const mapData = data.districts.map(function (name, i) {
    return { name, value: data.values[i] };
  });

  const chart = echarts.init(el, null, { renderer: 'canvas' });
  chart.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      formatter: function (p) {
        const v = p.value;
        if (v == null || v === '') return p.name + '<br/>暂无数据';
        return p.name + '<br/>现存确诊：' + Number(v).toLocaleString();
      },
    },
    visualMap: {
      type: 'continuous',
      min: 0,
      max: vmax > 0 ? vmax : 1,
      left: 12,
      bottom: '10%',
      text: ['高', '低'],
      calculable: true,
      itemWidth: 14,
      itemHeight: 130,
      inRange: {
        color: ['#0b2d4a', '#145a8d', '#1e88a8', '#5eb887', '#f2d349', '#ff6b35'],
      },
      textStyle: { color: '#8aa4bc', fontSize: 11 },
    },
    series: [
      {
        name: '现存确诊',
        type: 'map',
        map: 'HK_18',
        roam: true,
        scaleLimit: { min: 0.75, max: 5 },
        zoom: 1.05,
        selectedMode: false,
        label: {
          show: true,
          fontSize: 9,
          color: 'rgba(230, 245, 255, 0.92)',
        },
        emphasis: {
          label: { show: true, color: '#fff', fontSize: 10, fontWeight: 'bold' },
          itemStyle: {
            areaColor: 'rgba(255, 200, 80, 0.55)',
            borderColor: '#fff',
            borderWidth: 1,
          },
        },
        itemStyle: {
          borderColor: 'rgba(0, 212, 255, 0.55)',
          borderWidth: 1,
          shadowBlur: 6,
          shadowColor: 'rgba(0, 40, 80, 0.45)',
        },
        data: mapData,
      },
    ],
  });
  window.addEventListener('resize', function () {
    chart.resize();
  });
  return chart;
}

function initPie(el, data) {
  const chart = echarts.init(el);
  const pieData = data.levels.map((name, i) => ({
    name,
    value: data.values[i],
  }));
  chart.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: {
      orient: 'vertical',
      right: 8,
      top: 'middle',
      textStyle: { color: '#8aa4bc', fontSize: 11 },
    },
    series: [
      {
        type: 'pie',
        radius: ['38%', '68%'],
        center: ['42%', '52%'],
        avoidLabelOverlap: true,
        itemStyle: { borderRadius: 6, borderColor: '#0a1628', borderWidth: 2 },
        label: { color: '#c8d4e0', fontSize: 11 },
        data: pieData,
        color: ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452'],
      },
    ],
  });
  window.addEventListener('resize', () => chart.resize());
  return chart;
}

(async function () {
  try {
    const [ov, trend, geoJson, activeDist, cum, month, daily, risk] = await Promise.all([
      loadJson('/api/overview'),
      loadJson('/api/trend'),
      loadHkGeoJson(),
      loadJson('/api/district_active_distribution'),
      loadJson('/api/district_cumulative_top'),
      loadJson('/api/monthly_new'),
      loadJson('/api/district_daily_latest'),
      loadJson('/api/risk_distribution'),
    ]);

    setOverview(ov);
    initTrend(document.getElementById('chart-trend'), trend);

    const subEl = document.getElementById('chart-active-sub');
    if (subEl && activeDist.stat_date) {
      subEl.textContent = '统计日：' + activeDist.stat_date;
    }

    initActiveMapHeat(document.getElementById('chart-active-dist'), geoJson, activeDist);
    initBarH(document.getElementById('chart-cum'), cum);
    initBarV(document.getElementById('chart-month'), month);
    initBarDistrict(document.getElementById('chart-daily'), daily);

    if (risk.levels && risk.levels.length) {
      initPie(document.getElementById('chart-risk'), risk);
    } else {
      const el = document.getElementById('chart-risk');
      el.innerHTML =
        '<div style="display:flex;align-items:center;justify-content:center;min-height:160px;height:100%;color:#6a8aaa;font-size:13px;">暂无风险等级字段数据</div>';
    }
  } catch (e) {
    console.error(e);
    const layout = document.getElementById('chart-layout');
    if (layout) {
      layout.innerHTML =
        '<p style="padding:40px;color:#ff6b6b;grid-column:1/-1;">加载失败：' +
        e.message +
        '</p>';
    }
  }
})();
