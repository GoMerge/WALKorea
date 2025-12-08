import pandas as pd
import chardet

AVG_PATH = "data/avgWeather91_20.csv"
STATION_PATH = "data/station_info.csv"
OUTPUT_PATH = "data/avgWeather_with_fullname.csv"

def detect_encoding(file_path, num_bytes=10000):
    with open(file_path, 'rb') as f:
        rawdata = f.read(num_bytes)
    result = chardet.detect(rawdata)
    print(f"Detected encoding for {file_path}: {result['encoding']}")
    return result['encoding']

if __name__ == "__main__":
    enc_avg = detect_encoding(AVG_PATH)
    enc_station = detect_encoding(STATION_PATH)

    # ★ 핵심! header=2로 컬럼명/데이터 읽기
    df_avg = pd.read_csv(AVG_PATH, encoding=enc_avg or "euc-kr", header=2)
    df_station = pd.read_csv(STATION_PATH, encoding=enc_station or "euc-kr")

    print("df_avg columns:", list(df_avg.columns))
    print("df_station columns:", list(df_station.columns))

    # '지점번호' → '지점'으로 변경
    if "지점번호" in df_avg.columns:
        df_avg.rename(columns={"지점번호": "지점"}, inplace=True)

    df_station['full_name'] = df_station['지점주소']

    # 타입 통일(에러 방지용)
    df_avg['지점'] = df_avg['지점'].astype(str)
    df_station['지점'] = df_station['지점'].astype(str)

    df_merged = pd.merge(df_avg, df_station[['지점', 'full_name']], on='지점', how='left')

    print(df_merged[['지점', '지점명', '월', '날짜', '기온(℃)', 'full_name']].head())

    df_merged.to_csv(OUTPUT_PATH, encoding='cp949', index=False)
    print(f"병합 완료, 출력 파일: {OUTPUT_PATH}")
