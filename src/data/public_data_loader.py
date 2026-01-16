"""
공공데이터 연동 모듈 - 식품의약품안전처:식품영양성분DB정보 (파싱 로직 강화)
"""
import os
import json
import requests
import pandas as pd
from typing import List, Dict
from pathlib import Path
from dotenv import load_dotenv

from src.rag.knowledge_base import KnowledgeBase 

# .env 파일 로드
load_dotenv()

class PublicDataLoader:
    def __init__(self):
        # .env에서 Decoding 키를 가져옵니다.
        self.api_key = os.getenv("FOOD_SAFETY_API_KEY")
        
        if self.api_key:
            print(f"🔑 API 키 로드 성공: {self.api_key[:6]}...")
        else:
            print("⚠️ [오류] .env 파일에서 'FOOD_SAFETY_API_KEY'를 찾을 수 없습니다.")

        self.base_path = Path(__file__).parent.parent.parent / "data"
        self.kb = KnowledgeBase()
    
    def search_food_api(self, keyword: str, limit: int = 5) -> List[Dict]:
        """
        식품영양성분조회 API (getFoodNtrCpntDbInq02)
        """
        if not self.api_key:
            return []
        
        base_url = "http://apis.data.go.kr/1471000/FoodNtrCpntDbInfo02/getFoodNtrCpntDbInq02"
        
        params = {
            "serviceKey": self.api_key, 
            "pageNo": "1",
            "numOfRows": str(limit),
            "type": "json",
            "FOOD_NM_KR": keyword
        }
        
        try:
            response = requests.get(base_url, params=params, timeout=10)
            
            try:
                data = response.json()
            except json.JSONDecodeError:
                print(f"🔥 [API 오류] JSON 응답이 아닙니다. ({keyword})")
                return []
            
            # === [핵심 수정] 데이터 구조 유연하게 처리 ===
            header = data.get("header", {})
            if header.get("resultCode") != "00":
                # 데이터 없음은 에러 아님
                if "NODATA" in header.get("resultMsg", ""): 
                    return []
                print(f"❌ API 메시지: {header.get('resultMsg')}")
                return []
            
            body = data.get("body", {})
            items_raw = body.get("items", None)
            
            if not items_raw:
                return []
            
            # 구조가 딕셔너리인지 리스트인지 확인
            final_items = []
            
            if isinstance(items_raw, list):
                # 바로 리스트로 온 경우
                final_items = items_raw
            elif isinstance(items_raw, dict):
                # 딕셔너리로 감싸져서 온 경우 (items -> item)
                item_content = items_raw.get("item", [])
                if isinstance(item_content, list):
                    final_items = item_content
                elif isinstance(item_content, dict):
                    final_items = [item_content] # 하나만 온 경우
            else:
                return []

            foods = []
            for item in final_items:
                def safe_float(val):
                    try:
                        return float(val) if val and val not in ["N/A", ""] else 0.0
                    except:
                        return 0.0

                # 명세서 기준 필드 매핑
                food_info = {
                    "name": item.get("FOOD_NM_KR", ""),
                    "calories": safe_float(item.get("AMT_NUM1")), # 에너지
                    "protein": safe_float(item.get("AMT_NUM3")),  # 단백질
                    "fat": safe_float(item.get("AMT_NUM4")),      # 지방
                    "carbs": safe_float(item.get("AMT_NUM7")),    # 탄수화물
                    "source": "식품의약품안전처 API"
                }
                
                # 이름이 없는 데이터는 스킵
                if food_info["name"]:
                    foods.append(food_info)
                
            return foods
            
        except Exception as e:
            # 여기서 에러가 나면 무슨 에러인지 정확히 출력
            print(f"⚠️ 시스템 에러 ({keyword}): {e}")
            return []

    def fetch_and_upload_from_api(self, keywords: List[str]):
        print(f"\n🔍 API 자동 수집 시작 (키워드: {len(keywords)}개)")
        total_count = 0
        for keyword in keywords:
            print(f"   - '{keyword}' 검색 중...", end="")
            foods = self.search_food_api(keyword, limit=5)
            
            if not foods:
                print(" [결과 없음]")
                continue
            
            print(f" [OK] {len(foods)}개 발견 -> 업로드")
            
            documents = []
            for food in foods:
                content = f"{food['name']}: 칼로리 {food['calories']}kcal, 단백질 {food['protein']}g, 탄수화물 {food['carbs']}g, 지방 {food['fat']}g."
                documents.append({
                    "title": food['name'],
                    "content": content,
                    "source": "식품의약품안전처 API"
                })
            
            if documents:
                self.kb.add_documents(documents, category="food")
                total_count += len(documents)
        
        print(f"✅ API 데이터 총 {total_count}개 업로드 완료!")

    def upload_video_csv_to_supabase(self, filename: str):
        file_path = self.base_path / filename
        print(f"\n🎬 동영상 데이터 로딩 중: {file_path}")
        if not file_path.exists():
            print(f"❌ 파일을 찾을 수 없습니다: {filename}")
            return
        try:
            try: df = pd.read_csv(file_path, encoding='cp949')
            except: df = pd.read_csv(file_path, encoding='utf-8')
            
            documents = []
            for idx, row in df.iterrows():
                category_mid = row.get('중분류', '')
                category_sub = row.get('소분류', '') 
                title = row.get('제목', '')
                video_url = row.get('동영상주소', '')
                content = f"운동 영상. 분류: {category_mid} - {category_sub}. 제목: {title}. 이 운동은 {category_sub} 및 {category_mid}에 도움을 줍니다."
                documents.append({
                    "title": str(title),
                    "content": content,
                    "source": "국민체력100 유튜브",
                    "video_url": video_url,
                    "category": "video"
                })
            if documents:
                print(f"🎥 {len(documents)}개 동영상 데이터 업로드 시작...")
                self.kb.add_documents(documents, category="video")
                print("✅ 동영상 업로드 완료!")
        except Exception as e:
            print(f"❌ 업로드 실패: {e}")