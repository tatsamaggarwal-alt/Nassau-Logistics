# ============================================
# Nassau Logistics Intelligence Dashboard
# Developed by Tatsam Aggarwal
# © 2026 Tatsam Aggarwal. All rights reserved.
# ============================================

import streamlit as st
import plotly.express as px
from analysis import (
    load_and_process_data,
    route_analysis,
    ship_mode_analysis,
    service_tier_analysis,
    state_bottleneck_analysis,
    monthly_trend_analysis,
    route_drilldown,
    executive_kpis,
)

st.set_page_config(
    page_title="Nassau Logistics Intelligence",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    html, body, [class*="css"] {
        font-family: 'Segoe UI', sans-serif;
    }
    .main {
        background: linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%);
    }
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1500px;
    }
    div[data-testid="metric-container"] {
        background: white;
        border: 1px solid #e2e8f0;
        padding: 16px 18px;
        border-radius: 18px;
        box-shadow: 0 6px 18px rgba(15, 23, 42, 0.06);
    }
    .section-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 20px;
        padding: 18px 18px 10px 18px;
        box-shadow: 0 6px 18px rgba(15, 23, 42, 0.06);
        margin-bottom: 18px;
    }
    .hero-title {
        font-size: 2rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 0.1rem;
    }
    .hero-subtitle {
        color: #475569;
        font-size: 1rem;
        margin-bottom: 0.2rem;
    }
    .insight-box {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 14px 16px;
        margin-top: 8px;
        margin-bottom: 8px;
    }
    .footer-note {
        text-align: center;
        color: #64748b;
        font-size: 13px;
        padding-top: 18px;
        padding-bottom: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def get_data(delay_threshold: int):
    return load_and_process_data("data.csv", delay_threshold=delay_threshold)


st.markdown('<div class="hero-title">Nassau Candy Distributor</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-subtitle">Factory-to-Customer Shipping Route Efficiency Analysis</div>',
    unsafe_allow_html=True,
)
st.caption(
    "Executive logistics dashboard for route efficiency, geographic bottlenecks, ship mode tradeoffs, and state-level drill-down."
)

st.sidebar.header("Filters")
delay_threshold = st.sidebar.slider("Delay Threshold (days)", 1, 15, 5)

df = get_data(delay_threshold)

if df.empty:
    st.error("No valid data available after cleaning.")
    st.stop()

min_date = df["Order Date"].min().date()
max_date = df["Order Date"].max().date()

date_range = st.sidebar.date_input(
    "Order Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

region_options = ["All"] + sorted(df["Region"].dropna().astype(str).unique().tolist())
state_options = ["All"] + sorted(df["State/Province"].dropna().astype(str).unique().tolist())
ship_options = ["All"] + sorted(df["Ship Mode"].dropna().astype(str).unique().tolist())
factory_options = ["All"] + sorted(df["Factory"].dropna().astype(str).unique().tolist())

region_filter = st.sidebar.selectbox("Region", region_options)
state_filter = st.sidebar.selectbox("State", state_options)
ship_filter = st.sidebar.selectbox("Ship Mode", ship_options)
factory_filter = st.sidebar.selectbox("Factory", factory_options)
route_level = st.sidebar.radio("Route Definition", ["Factory → State", "Factory → Region"], index=0)

filtered_df = df[
    (df["Order Date"].dt.date >= start_date) &
    (df["Order Date"].dt.date <= end_date)
].copy()

if region_filter != "All":
    filtered_df = filtered_df[filtered_df["Region"] == region_filter]

if state_filter != "All":
    filtered_df = filtered_df[filtered_df["State/Province"] == state_filter]

if ship_filter != "All":
    filtered_df = filtered_df[filtered_df["Ship Mode"] == ship_filter]

if factory_filter != "All":
    filtered_df = filtered_df[filtered_df["Factory"] == factory_filter]

if filtered_df.empty:
    st.warning("No records match the selected filters.")
    st.stop()

route_type = "state" if route_level == "Factory → State" else "region"

route_df = route_analysis(filtered_df, route_type=route_type)
ship_df = ship_mode_analysis(filtered_df)
tier_df = service_tier_analysis(filtered_df)
state_df = state_bottleneck_analysis(filtered_df)
trend_df = monthly_trend_analysis(filtered_df)
kpis = executive_kpis(filtered_df, route_type=route_type)

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Shipments", f"{kpis['total_shipments']:,}")
k2.metric("Avg Lead Time", f"{kpis['avg_lead_time']:.2f} days")
k3.metric("Delay Frequency", f"{kpis['delay_frequency_pct']:.2f}%")
k4.metric("Best Route", kpis["best_route"])
k5.metric("Worst Route", kpis["worst_route"])

left, right = st.columns([1.35, 1])

with left:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Route Efficiency Overview")

    route_display = route_df.copy()
    route_display["avg_lead_time"] = route_display["avg_lead_time"].round(2)
    route_display["median_lead_time"] = route_display["median_lead_time"].round(2)
    route_display["std_lead_time"] = route_display["std_lead_time"].round(2)
    route_display["delay_rate_pct"] = route_display["delay_rate_pct"].round(2)
    route_display["efficiency_score"] = route_display["efficiency_score"].round(2)

    route_col = "Route_State" if route_type == "state" else "Route_Region"

    route_display = route_display.rename(columns={
        route_col: "Route",
        "total_shipments": "Shipment Volume",
        "avg_lead_time": "Avg Lead Time",
        "median_lead_time": "Median Lead Time",
        "std_lead_time": "Variability",
        "delay_rate_pct": "Delay %",
        "efficiency_score": "Efficiency Score",
        "route_health": "Route Health",
        "avg_sales": "Avg Sales",
        "avg_cost": "Avg Cost",
        "avg_gross_profit": "Avg Gross Profit",
    })

    st.dataframe(route_display, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

with right:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Executive Summary")

    worst_state = state_df.iloc[0]["State/Province"] if not state_df.empty else "N/A"
    bottleneck_count = int((state_df["bottleneck_flag"] == "Yes").sum()) if not state_df.empty else 0

    st.markdown(
        f"""
- The filtered network averages **{kpis['avg_lead_time']:.2f} days** of shipping lead time.
- **{kpis['delay_frequency_pct']:.2f}%** of shipments exceed the selected delay threshold.
- The best-performing route is **{kpis['best_route']}**.
- The weakest route is **{kpis['worst_route']}**.
- **{worst_state}** is currently the most delayed state in this filtered view.
- **{bottleneck_count}** states are flagged as likely bottlenecks based on both shipment volume and lead time.
        """
    )

    st.markdown('<div class="insight-box">', unsafe_allow_html=True)
    st.markdown(
        "Priority should go first to high-volume routes with weak efficiency scores and states where faster shipping classes still fail to reduce delays materially."
    )
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

c1, c2 = st.columns(2)

with c1:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Top 10 Most Efficient Routes")
    route_col = "Route_State" if route_type == "state" else "Route_Region"
    top10 = route_df.head(10).sort_values("efficiency_score", ascending=True)
    fig_top = px.bar(
        top10,
        x="efficiency_score",
        y=route_col,
        orientation="h",
        text="efficiency_score",
        color="efficiency_score",
        color_continuous_scale="Blues",
    )
    fig_top.update_traces(texttemplate="%{text:.1f}", textposition="outside")
    fig_top.update_layout(height=430, coloraxis_showscale=False, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_top, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with c2:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Bottom 10 Least Efficient Routes")
    bottom10 = route_df.tail(10).sort_values("avg_lead_time", ascending=True)
    fig_bottom = px.bar(
        bottom10,
        x="avg_lead_time",
        y=route_col,
        orientation="h",
        text="avg_lead_time",
        color="avg_lead_time",
        color_continuous_scale="Reds",
    )
    fig_bottom.update_traces(texttemplate="%{text:.1f}", textposition="outside")
    fig_bottom.update_layout(height=430, coloraxis_showscale=False, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_bottom, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

c3, c4 = st.columns(2)

with c3:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Route Volume vs Lead Time")
    fig_scatter = px.scatter(
        route_df,
        x="total_shipments",
        y="avg_lead_time",
        size="delay_rate_pct",
        color="efficiency_score",
        hover_name=route_col,
        color_continuous_scale="Viridis",
    )
    fig_scatter.update_layout(height=420, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_scatter, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with c4:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Monthly Lead Time Trend")
    if not trend_df.empty and len(trend_df) > 1:
        fig_trend = px.line(
            trend_df,
            x="Order Month",
            y="avg_lead_time",
            markers=True,
        )
        fig_trend.update_layout(height=420, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("Not enough monthly variation to show a trend.")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.subheader("Geographic Bottleneck Analysis")
tab_map, tab_table = st.tabs(["US State Heatmap", "Bottleneck States"])

with tab_map:
    fig_map = px.choropleth(
        state_df,
        locations="State Code",
        locationmode="USA-states",
        color="avg_lead_time",
        scope="usa",
        hover_data={
            "State/Province": True,
            "total_shipments": True,
            "delay_rate_pct": ':.1f',
            "avg_lead_time": ':.2f',
            "State Code": False,
        },
        color_continuous_scale="Reds",
    )
    fig_map.update_layout(height=560, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_map, use_container_width=True)

with tab_table:
    bottlenecks = state_df[state_df["bottleneck_flag"] == "Yes"].copy()
    if bottlenecks.empty:
        st.info("No bottleneck states detected for the selected filters.")
    else:
        bottlenecks = bottlenecks.rename(columns={
            "State/Province": "State",
            "avg_lead_time": "Avg Lead Time",
            "median_lead_time": "Median Lead Time",
            "total_shipments": "Shipment Volume",
            "delay_rate_pct": "Delay %",
        })
        st.dataframe(
            bottlenecks[["State", "Avg Lead Time", "Median Lead Time", "Shipment Volume", "Delay %"]],
            use_container_width=True,
            hide_index=True,
        )
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.subheader("Ship Mode Performance & Cost-Time Tradeoff")
st.caption("Compare Standard Class, First Class, Second Class, and Same Day on speed, reliability, consistency, and profitability.")

if ship_df.empty:
    st.info("Ship mode data is unavailable for the current filters.")
else:
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Fastest Mode", ship_df.loc[ship_df["avg_lead_time"].idxmin(), "Ship Mode"])
    s2.metric("Lowest Delay %", ship_df.loc[ship_df["delay_rate_pct"].idxmin(), "Ship Mode"])
    s3.metric("Highest Avg Gross Profit", ship_df.loc[ship_df["avg_gross_profit"].idxmax(), "Ship Mode"])
    s4.metric("Highest Volume", ship_df.loc[ship_df["total_orders"].idxmax(), "Ship Mode"])

    ship_tab1, ship_tab2, ship_tab3, ship_tab4 = st.tabs(
        ["Speed", "Reliability", "Cost-Time Tradeoff", "Standard vs Faster Classes"]
    )

    with ship_tab1:
        a, b = st.columns(2)

        with a:
            fig_lead = px.bar(
                ship_df.sort_values("avg_lead_time"),
                x="Ship Mode",
                y="avg_lead_time",
                text="avg_lead_time",
                color="Ship Mode",
            )
            fig_lead.update_traces(texttemplate="%{text:.2f}", textposition="outside")
            fig_lead.update_layout(showlegend=False, height=390, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_lead, use_container_width=True)

        with b:
            fig_median = px.bar(
                ship_df.sort_values("median_lead_time"),
                x="Ship Mode",
                y="median_lead_time",
                text="median_lead_time",
                color="Ship Mode",
            )
            fig_median.update_traces(texttemplate="%{text:.2f}", textposition="outside")
            fig_median.update_layout(showlegend=False, height=390, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_median, use_container_width=True)

    with ship_tab2:
        a, b = st.columns(2)

        with a:
            fig_delay = px.bar(
                ship_df.sort_values("delay_rate_pct"),
                x="Ship Mode",
                y="delay_rate_pct",
                text="delay_rate_pct",
                color="Ship Mode",
            )
            fig_delay.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
            fig_delay.update_layout(showlegend=False, height=390, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_delay, use_container_width=True)

        with b:
            fig_std = px.bar(
                ship_df.sort_values("std_lead_time"),
                x="Ship Mode",
                y="std_lead_time",
                text="std_lead_time",
                color="Ship Mode",
            )
            fig_std.update_traces(texttemplate="%{text:.2f}", textposition="outside")
            fig_std.update_layout(showlegend=False, height=390, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_std, use_container_width=True)

    with ship_tab3:
        fig_tradeoff = px.scatter(
            ship_df,
            x="avg_lead_time",
            y="avg_gross_profit",
            size="total_orders",
            color="Ship Mode",
            hover_data={
                "avg_cost": ':.2f',
                "avg_sales": ':.2f',
                "delay_rate_pct": ':.1f'
            }
        )
        fig_tradeoff.update_layout(height=430, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_tradeoff, use_container_width=True)

        ship_display = ship_df.rename(columns={
            "total_orders": "Orders",
            "avg_lead_time": "Avg Lead Time",
            "median_lead_time": "Median Lead Time",
            "std_lead_time": "Variability",
            "delay_rate_pct": "Delay %",
            "avg_sales": "Avg Sales",
            "avg_cost": "Avg Cost",
            "avg_gross_profit": "Avg Gross Profit",
        }).round(2)
        st.dataframe(ship_display, use_container_width=True, hide_index=True)

    with ship_tab4:
        tier_display = tier_df.rename(columns={
            "Service Tier": "Service Tier",
            "total_orders": "Orders",
            "avg_lead_time": "Avg Lead Time",
            "median_lead_time": "Median Lead Time",
            "std_lead_time": "Variability",
            "delay_rate_pct": "Delay %",
            "avg_sales": "Avg Sales",
            "avg_cost": "Avg Cost",
            "avg_gross_profit": "Avg Gross Profit",
        }).round(2)

        st.dataframe(tier_display, use_container_width=True, hide_index=True)

        st.markdown('<div class="insight-box">', unsafe_allow_html=True)
        st.markdown(
            "This summary groups **Standard Class** against **Faster Service Classes** (First Class, Second Class, and Same Day) to support descriptive evaluation of the cost-time tradeoff."
        )
        st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.subheader("Route Drill-Down")

d1, d2, d3 = st.columns(3)
drill_factory = d1.selectbox("Drill-Down Factory", sorted(filtered_df["Factory"].dropna().unique()))
drill_ship = d2.selectbox("Drill-Down Ship Mode", ["All"] + sorted(filtered_df["Ship Mode"].dropna().unique()))
drill_state = d3.selectbox("Drill-Down State", ["All"] + sorted(filtered_df["State/Province"].dropna().unique()))

drill_df = route_drilldown(filtered_df, factory=drill_factory, state=drill_state, ship_mode=drill_ship)

if drill_df.empty:
    st.info("No drill-down data available for the selected combination.")
else:
    drill_route_df = route_analysis(drill_df, route_type="state")

    x1, x2 = st.columns([1.1, 1])

    with x1:
        drill_display = drill_route_df.rename(columns={
            "Route_State": "Route",
            "total_shipments": "Shipment Volume",
            "avg_lead_time": "Avg Lead Time",
            "median_lead_time": "Median Lead Time",
            "std_lead_time": "Variability",
            "delay_rate_pct": "Delay %",
            "efficiency_score": "Efficiency Score",
            "route_health": "Route Health",
            "avg_sales": "Avg Sales",
            "avg_cost": "Avg Cost",
            "avg_gross_profit": "Avg Gross Profit",
        }).round(2)
        st.dataframe(drill_display, use_container_width=True, hide_index=True)

    with x2:
        drill_trend = monthly_trend_analysis(drill_df)
        if not drill_trend.empty and len(drill_trend) > 1:
            fig_drill = px.line(
                drill_trend,
                x="Order Month",
                y="avg_lead_time",
                markers=True,
                title="Route Trend Over Time",
            )
            fig_drill.update_layout(height=340, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig_drill, use_container_width=True)
        else:
            st.info("Not enough monthly variation to show route trend.")

    order_cols = [
        col for col in [
            "Order ID", "Order Date", "Ship Date", "Factory", "Ship Mode",
            "Region", "State/Province", "Product Name", "Units",
            "Sales", "Cost", "Gross Profit", "Lead Time"
        ] if col in drill_df.columns
    ]

    st.markdown("#### Order-Level Shipment Timeline")
    st.dataframe(
        drill_df[order_cols].sort_values(["Order Date", "Ship Date"]),
        use_container_width=True,
        hide_index=True,
    )

st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.subheader("Order-Level Lead Time Distribution")
fig_hist = px.histogram(
    filtered_df,
    x="Lead Time",
    nbins=25,
    marginal="box",
)
fig_hist.update_layout(height=420, margin=dict(l=10, r=10, t=10, b=10))
st.plotly_chart(fig_hist, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.subheader("Strategic Recommendations")
recommendations = [
    "Prioritize high-volume bottleneck states where average lead time stays above the network median.",
    "Focus route optimization efforts first on bottom-ranked factory-to-customer routes with both high shipment volume and high delay rates.",
    "Use faster service classes selectively where they materially reduce lead time or delay frequency relative to Standard Class.",
    "Investigate states where faster service classes still underperform, since that signals geographic or operational bottlenecks rather than mode choice.",
    "Use route-level variability and delay rate alongside average lead time before making logistics allocation decisions."
]
for i, rec in enumerate(recommendations, start=1):
    st.markdown(f"{i}. {rec}")
st.markdown('</div>', unsafe_allow_html=True)

st.markdown(
    """
    <div class="footer-note">
        Dashboard developed by <b>Tatsam Aggarwal</b> · © 2026 Tatsam Aggarwal. All rights reserved.
    </div>
    """,
    unsafe_allow_html=True,
)
