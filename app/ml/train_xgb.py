import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
import os

df = pd.read_csv('data/avgWeather_with_fullname.csv', encoding='cp949')

df.rename(columns={
    "기온(℃)": "temperature",
    "강수량\n(mm)": "precipitation",
    "월": "month",
    "날짜": "day",
    "Unnamed: 7": "temp_std"
}, inplace=True)

df['weekday'] = 0

for col in ['month', 'day', 'weekday', 'temperature', 'precipitation', 'temp_std']:
    df[col] = pd.to_numeric(df[col], errors='coerce')

df['target'] = df['temperature'].shift(-1)
df = df.dropna()

X = df[['month', 'day', 'weekday', 'temperature', 'precipitation', 'temp_std']]
y = df['target']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

model = xgb.XGBRegressor()
model.fit(X_train, y_train)
model.save_model("app/ml/xgb_weather_model.json")
print("모델 저장 완료:", "app/ml/xgb_weather_model.json")
print("모델 파일 크기:", os.path.getsize("app/ml/xgb_weather_model.json"), "bytes")
