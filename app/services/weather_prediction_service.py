import pandas as pd
import xgboost as xgb
from typing import Optional
from datetime import datetime


model_path = "app/ml/xgb_weather_model.json"
model = xgb.XGBRegressor()
model.load_model(model_path)


def preprocess_input(date_str: str, temperature: float, precipitation: float):
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return pd.DataFrame({
        "month": [dt.month],
        "day": [dt.day],
        "weekday": [dt.weekday()],
        "temperature": [temperature],
        "precipitation": [precipitation],
        "temp_std": [0.0],
    })


def predict_temperature(date_str: str, temperature: float, precipitation: float) -> Optional[float]:
    input_df = preprocess_input(date_str, temperature, precipitation)
    pred = model.predict(input_df)
    return float(pred[0])
