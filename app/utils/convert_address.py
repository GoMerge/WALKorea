import requests
import os
from dotenv import load_dotenv

load_dotenv()

KAKAO_REST_API_KEY = os.getenv("KAKAO_REST_API_KEY")

def convert_address_to_coordinates(address: str):
    print(f"KAKAO_REST_API_KEY: {KAKAO_REST_API_KEY}")
    try:
        url = f"https://dapi.kakao.com/v2/local/search/address.json?query={address}"
        headers = {"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"}
        resp = requests.get(url, headers=headers, timeout=5)
        resp.raise_for_status()
        docs = resp.json().get("documents")
        if docs:
            lat = float(docs[0]["y"])
            lon = float(docs[0]["x"])
            return lat, lon
        return None
    except requests.RequestException as e:
        print(f"[Kakao API Error] 주소 변환 요청 실패: {e}")
        return None
