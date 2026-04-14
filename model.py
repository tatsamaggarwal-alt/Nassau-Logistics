# ============================================
# Nassau Logistics Intelligence Dashboard
# Optional ML Utility
# Developed by Tatsam Aggarwal
# © 2026 Tatsam Aggarwal. All rights reserved.
# ============================================

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score


def train_model(df: pd.DataFrame):
    data = df.copy()
    data = data.dropna(subset=["Ship Mode", "Region", "State/Province", "Lead Time"])

    data = pd.get_dummies(
        data[["Ship Mode", "Region", "State/Province", "Lead Time"]],
        columns=["Ship Mode", "Region", "State/Province"],
        drop_first=True
    )

    X = data.drop(columns=["Lead Time"])
    y = data["Lead Time"]

    if len(data) < 20:
        raise ValueError("Not enough data to train the model.")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = RandomForestRegressor(n_estimators=150, random_state=42)
    model.fit(X_train, y_train)

    preds = model.predict(X_test)

    metrics = {
        "MAE": round(mean_absolute_error(y_test, preds), 2),
        "R2 Score": round(r2_score(y_test, preds), 2),
    }

    return model, X.columns.tolist(), metrics
