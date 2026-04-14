# ============================================
# Nassau Logistics Intelligence Dashboard
# Developed by Tatsam Aggarwal
# © 2026 Tatsam Aggarwal. All rights reserved.
# ============================================

import pandas as pd
import numpy as np


PRODUCT_FACTORY_MAP = {
    "Wonka Bar - Nutty Crunch Surprise": "Lot's O' Nuts",
    "Wonka Bar - Fudge Mallows": "Lot's O' Nuts",
    "Wonka Bar -Scrumdiddlyumptious": "Lot's O' Nuts",
    "Wonka Bar - Milk Chocolate": "Wicked Choccy's",
    "Wonka Bar - Triple Dazzle Caramel": "Wicked Choccy's",
    "Laffy Taffy": "Sugar Shack",
    "SweeTARTS": "Sugar Shack",
    "Nerds": "Sugar Shack",
    "Fun Dip": "Sugar Shack",
    "Fizzy Lifting Drinks": "Sugar Shack",
    "Everlasting Gobstopper": "Secret Factory",
    "Hair Toffee": "The Other Factory",
    "Lickable Wallpaper": "Secret Factory",
    "Wonka Gum": "Secret Factory",
    "Kazookles": "The Other Factory"
}

FACTORY_COORDS = {
    "Lot's O' Nuts": (32.881893, -111.768036),
    "Wicked Choccy's": (32.076176, -81.088371),
    "Sugar Shack": (48.11914, -96.18115),
    "Secret Factory": (41.446333, -90.565487),
    "The Other Factory": (35.1175, -89.971107),
    "Unknown": (39.50, -98.35)
}

STATE_ABBR = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
    "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
    "District of Columbia": "DC", "Florida": "FL", "Georgia": "GA", "Hawaii": "HI",
    "Idaho": "ID", "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS",
    "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
    "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS",
    "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV",
    "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
    "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK",
    "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
    "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT",
    "Vermont": "VT", "Virginia": "VA", "Washington": "WA", "West Virginia": "WV",
    "Wisconsin": "WI", "Wyoming": "WY"
}


def _route_health(score: float) -> str:
    if score >= 80:
        return "Efficient"
    if score >= 60:
        return "Stable"
    if score >= 40:
        return "Risky"
    return "Bottleneck"


def load_and_process_data(file_path: str, delay_threshold: int = 5) -> pd.DataFrame:
    try:
        df = pd.read_csv(file_path)
    except Exception as exc:
        raise Exception("❌ Error loading data.csv") from exc

    for col in ["Order Date", "Ship Date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], dayfirst=True, errors="coerce")

    for col in ["Sales", "Cost", "Gross Profit", "Units"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    required_cols = ["Order Date", "Ship Date", "Product Name", "State/Province", "Ship Mode", "Region"]
    available_required = [col for col in required_cols if col in df.columns]
    df = df.dropna(subset=available_required).copy()

    df["Lead Time"] = (df["Ship Date"] - df["Order Date"]).dt.days
    df = df[df["Lead Time"].notna()].copy()
    df = df[df["Lead Time"] >= 0].copy()

    df["Factory"] = df["Product Name"].map(PRODUCT_FACTORY_MAP).fillna("Unknown")

    df["Factory Latitude"] = df["Factory"].map(lambda x: FACTORY_COORDS.get(x, FACTORY_COORDS["Unknown"])[0])
    df["Factory Longitude"] = df["Factory"].map(lambda x: FACTORY_COORDS.get(x, FACTORY_COORDS["Unknown"])[1])

    df["State Code"] = df["State/Province"].map(STATE_ABBR).fillna(df["State/Province"])
    df["Route_State"] = df["Factory"] + " → " + df["State/Province"].astype(str)
    df["Route_Region"] = df["Factory"] + " → " + df["Region"].astype(str)

    faster_classes = {"First Class", "Second Class", "Same Day"}
    df["Service Tier"] = np.where(
        df["Ship Mode"].isin(faster_classes),
        "Faster Service Classes",
        "Standard Class"
    )

    df["Delayed"] = (df["Lead Time"] > delay_threshold).astype(int)
    df["Order Month"] = df["Order Date"].dt.to_period("M").dt.to_timestamp()

    return df


def route_analysis(df: pd.DataFrame, route_type: str = "state") -> pd.DataFrame:
    route_col = "Route_State" if route_type.lower() == "state" else "Route_Region"

    route_df = df.groupby(route_col).agg(
        total_shipments=("Order ID", "count"),
        avg_lead_time=("Lead Time", "mean"),
        median_lead_time=("Lead Time", "median"),
        std_lead_time=("Lead Time", "std"),
        delay_rate=("Delayed", "mean"),
        avg_sales=("Sales", "mean"),
        avg_cost=("Cost", "mean"),
        avg_gross_profit=("Gross Profit", "mean")
    ).reset_index()

    route_df["std_lead_time"] = route_df["std_lead_time"].fillna(0)

    max_lead = route_df["avg_lead_time"].max()
    min_lead = route_df["avg_lead_time"].min()

    if pd.isna(max_lead) or pd.isna(min_lead) or max_lead == min_lead:
        route_df["efficiency_score"] = 100.0
    else:
        route_df["efficiency_score"] = 100 - (
            (route_df["avg_lead_time"] - min_lead) / (max_lead - min_lead) * 100
        )

    route_df["delay_rate_pct"] = route_df["delay_rate"] * 100
    route_df["route_health"] = route_df["efficiency_score"].apply(_route_health)

    return route_df.sort_values(
        by=["efficiency_score", "total_shipments"],
        ascending=[False, False]
    ).reset_index(drop=True)


def ship_mode_analysis(df: pd.DataFrame) -> pd.DataFrame:
    ship_df = df.groupby("Ship Mode").agg(
        avg_lead_time=("Lead Time", "mean"),
        median_lead_time=("Lead Time", "median"),
        std_lead_time=("Lead Time", "std"),
        delay_rate=("Delayed", "mean"),
        total_orders=("Order ID", "count"),
        avg_sales=("Sales", "mean"),
        avg_cost=("Cost", "mean"),
        avg_gross_profit=("Gross Profit", "mean")
    ).reset_index()

    ship_df["std_lead_time"] = ship_df["std_lead_time"].fillna(0)
    ship_df["delay_rate_pct"] = ship_df["delay_rate"] * 100

    return ship_df.sort_values("avg_lead_time").reset_index(drop=True)


def service_tier_analysis(df: pd.DataFrame) -> pd.DataFrame:
    tier_df = df.groupby("Service Tier").agg(
        avg_lead_time=("Lead Time", "mean"),
        median_lead_time=("Lead Time", "median"),
        std_lead_time=("Lead Time", "std"),
        delay_rate=("Delayed", "mean"),
        total_orders=("Order ID", "count"),
        avg_sales=("Sales", "mean"),
        avg_cost=("Cost", "mean"),
        avg_gross_profit=("Gross Profit", "mean")
    ).reset_index()

    tier_df["std_lead_time"] = tier_df["std_lead_time"].fillna(0)
    tier_df["delay_rate_pct"] = tier_df["delay_rate"] * 100

    return tier_df.sort_values("avg_lead_time").reset_index(drop=True)


def state_bottleneck_analysis(df: pd.DataFrame) -> pd.DataFrame:
    state_df = df.groupby(["State/Province", "State Code"]).agg(
        avg_lead_time=("Lead Time", "mean"),
        median_lead_time=("Lead Time", "median"),
        total_shipments=("Order ID", "count"),
        delay_rate=("Delayed", "mean")
    ).reset_index()

    state_df["delay_rate_pct"] = state_df["delay_rate"] * 100

    median_lead = state_df["avg_lead_time"].median()
    median_volume = state_df["total_shipments"].median()

    state_df["bottleneck_flag"] = np.where(
        (state_df["avg_lead_time"] > median_lead) &
        (state_df["total_shipments"] > median_volume),
        "Yes",
        "No"
    )

    return state_df.sort_values(
        by=["avg_lead_time", "total_shipments"],
        ascending=[False, False]
    ).reset_index(drop=True)


def monthly_trend_analysis(df: pd.DataFrame) -> pd.DataFrame:
    trend_df = df.groupby("Order Month").agg(
        avg_lead_time=("Lead Time", "mean"),
        total_shipments=("Order ID", "count"),
        delay_rate=("Delayed", "mean")
    ).reset_index()

    trend_df["delay_rate_pct"] = trend_df["delay_rate"] * 100
    return trend_df.sort_values("Order Month").reset_index(drop=True)


def route_drilldown(df: pd.DataFrame, factory: str = None, state: str = None, ship_mode: str = None) -> pd.DataFrame:
    drill_df = df.copy()

    if factory and factory != "All":
        drill_df = drill_df[drill_df["Factory"] == factory]
    if state and state != "All":
        drill_df = drill_df[drill_df["State/Province"] == state]
    if ship_mode and ship_mode != "All":
        drill_df = drill_df[drill_df["Ship Mode"] == ship_mode]

    return drill_df.sort_values(["Order Date", "Ship Date"]).reset_index(drop=True)


def executive_kpis(df: pd.DataFrame, route_type: str = "state") -> dict:
    if df.empty:
        return {
            "total_shipments": 0,
            "avg_lead_time": 0.0,
            "delay_frequency_pct": 0.0,
            "best_route": "N/A",
            "worst_route": "N/A"
        }

    route_df = route_analysis(df, route_type=route_type)
    route_col = "Route_State" if route_type == "state" else "Route_Region"

    return {
        "total_shipments": int(len(df)),
        "avg_lead_time": round(df["Lead Time"].mean(), 2),
        "delay_frequency_pct": round(df["Delayed"].mean() * 100, 2),
        "best_route": route_df.iloc[0][route_col] if not route_df.empty else "N/A",
        "worst_route": route_df.iloc[-1][route_col] if not route_df.empty else "N/A",
    }
