# Nassau Logistics Intelligence Dashboard

Factory-to-Customer Shipping Route Efficiency Analysis for Nassau Candy Distributor.

## Developed By
**Tatsam Aggarwal**  
© 2026 Tatsam Aggarwal. All rights reserved.

## Project Overview
This dashboard analyzes shipping route efficiency from factory to customer locations across the US. It helps identify the most efficient routes, least efficient routes, bottleneck states, and ship mode tradeoffs using logistics and commercial metrics.

## Features
- Route efficiency overview
- Top 10 and bottom 10 route analysis
- Geographic bottleneck analysis
- Ship mode performance comparison
- Standard vs faster service class comparison
- Route drill-down
- Order-level shipment timeline
- Strategic recommendations

## Files
- `app.py` → Streamlit dashboard
- `analysis.py` → data cleaning, feature engineering, aggregations
- `model.py` → optional ML utility
- `data.csv` → dataset
- `requirements.txt` → dependencies
- `Dockerfile` → container setup

## Run Locally

Install dependencies:

```bash
pip install -r requirements.txt