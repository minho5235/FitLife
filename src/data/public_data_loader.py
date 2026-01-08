"""
공공데이터 연동 모듈 - API + 파일 변환
"""
import os
import json
import requests
import pandas as pd
from typing import List, Dict
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class PublicDataLoader:
    def __init__(self):
        self.api_key = os.getenv("FOOD_SAFETY_API_KEY", "")
        self.base_path = Path(__file__).parent.parent.parent / "data"
    
    def search_food_api(self, keyword: str, limit: int = 10) -> List[Dict]:
        """식품안전나라 API로 식품 검색"""
        if not self.api_key:
            return []
        
        url = "http://apis.data.go.kr/1471000/FoodNtrIrdntInfoService1/getFoodNtrItdntList1"
        params = {
            "serviceKey": self.api_key,
            "pageNo": "1",
            "numOfRows": str(limit),
            "type": "json",
            "FOOD_NM_KR": keyword
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            items = data.get("body", {}).get("items", [])
            
            foods = []
            for item in items:
                foods.append({
                    "name": item.get("FOOD_NM_KR", ""),
                    "calories": float(item.get("AMT_NUM1", 0) or 0),
                    "protein": float(item.get("AMT_NUM3", 0) or 0),
                    "fat": float(item.get("AMT_NUM4", 0) or 0),
                    "carbs": float(item.get("AMT_NUM7", 0) or 0),
                    "source": "식품안전나라"
                })
            return foods
        except:
            return []
    
    def convert_csv_to_json(self, csv_path: str, output_name: str) -> str:
        """CSV/Excel을 JSON으로 변환"""
        try:
            if csv_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(csv_path)
            else:
                df = pd.read_csv(csv_path, encoding='utf-8')
            
            output_path = self.base_path / "processed" / output_name
            df.to_json(output_path, orient='records', force_ascii=False)
            return str(output_path)
        except Exception as e:
            return f"변환 실패: {e}"
