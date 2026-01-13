"""
이미지 분석 모듈 v2.0
- 냉장고/식재료 사진 → 재료 인식 → 요리 추천
- 운동기구 사진 → 기구 인식 → 운동 추천
"""
import base64
import json
from typing import List, Dict, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from src.config import GOOGLE_API_KEY


class ImageAnalyzer:
    """통합 이미지 분석기 - 식재료 & 운동기구"""
    
    def __init__(self):
        self.vision_model = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=GOOGLE_API_KEY,
            temperature=0.3
        )
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=GOOGLE_API_KEY,
            temperature=0.7
        )
    
    def _encode_image(self, image_bytes: bytes) -> str:
        return base64.b64encode(image_bytes).decode("utf-8")
    
    def _parse_json_response(self, text: str) -> Dict:
        try:
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            return json.loads(text.strip())
        except:
            return {}
    
    def analyze_ingredients(self, image_bytes: bytes) -> Dict:
        """냉장고/식재료 사진 분석"""
        image_data = self._encode_image(image_bytes)
        
        prompt = """이 사진에서 식별 가능한 모든 식재료를 분석해주세요.

반드시 아래 JSON 형식으로만 응답:
{
    "ingredients": [
        {"name": "재료명", "quantity": "양", "category": "채소/과일/육류/해산물/유제품/곡물/조미료/음료/기타", "freshness": "신선/보통/주의"}
    ],
    "total_confidence": 0.0~1.0
}"""
        
        message = HumanMessage(content=[
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
        ])
        
        try:
            response = self.vision_model.invoke([message])
            result = self._parse_json_response(response.content)
            if result:
                result["success"] = True
                return result
            return {"success": False, "error": "파싱 실패", "ingredients": []}
        except Exception as e:
            return {"success": False, "error": str(e), "ingredients": []}
    
    def suggest_recipes(self, ingredients: List[str], dietary_restrictions: List[str] = None, meal_type: str = "any") -> Dict:
        """재료 기반 요리 추천"""
        restrictions_text = f"\n제한사항: {', '.join(dietary_restrictions)} 제외" if dietary_restrictions else ""
        
        prompt = f"""사용 가능한 재료: {', '.join(ingredients)}{restrictions_text}

이 재료로 만들 수 있는 요리 3가지를 추천해주세요.
반드시 아래 JSON 형식으로만 응답:
{{"recipes": [{{"name": "요리명", "description": "설명", "cooking_time": "시간", "difficulty": "쉬움/보통/어려움", "nutrition": {{"calories": 숫자, "protein": 숫자}}, "steps": ["단계1", "단계2"]}}]}}"""
        
        try:
            response = self.llm.invoke(prompt)
            result = self._parse_json_response(response.content)
            if result:
                result["success"] = True
                return result
            return {"success": False, "recipes": []}
        except Exception as e:
            return {"success": False, "error": str(e), "recipes": []}
    
    def analyze_equipment(self, image_bytes: bytes) -> Dict:
        """운동기구/환경 사진 분석"""
        image_data = self._encode_image(image_bytes)
        
        prompt = """이 사진에서 운동 관련 기구와 환경을 분석해주세요.

반드시 아래 JSON 형식으로만 응답:
{
    "equipment": [{"name": "기구명", "category": "유산소기구/웨이트기구/소도구/맨몸운동/기타"}],
    "environment": "홈트레이닝/헬스장/야외/기타",
    "available_space": "넓음/보통/좁음"
}"""
        
        message = HumanMessage(content=[
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
        ])
        
        try:
            response = self.vision_model.invoke([message])
            result = self._parse_json_response(response.content)
            if result:
                result["success"] = True
                return result
            return {"success": False, "equipment": []}
        except Exception as e:
            return {"success": False, "error": str(e), "equipment": []}
    
    def suggest_exercises(self, equipment: List[str], target_area: str = "전신", fitness_level: str = "중급", duration: int = 30, health_conditions: List[str] = None) -> Dict:
        """기구 기반 운동 추천"""
        conditions_text = f"\n건강 상태: {', '.join(health_conditions)}" if health_conditions else ""
        
        prompt = f"""사용 가능한 기구: {', '.join(equipment) if equipment else '맨몸'}
목표 부위: {target_area}, 수준: {fitness_level}, 시간: {duration}분{conditions_text}

운동 루틴을 추천해주세요.
반드시 JSON 형식으로만 응답:
{{"routine_name": "이름", "estimated_calories": 숫자, "warmup": [{{"name": "운동명", "duration": "시간"}}], "main_workout": [{{"name": "운동명", "sets": 숫자, "reps": "횟수", "rest": "휴식", "target_muscle": "부위"}}], "cooldown": [{{"name": "운동명", "duration": "시간"}}]}}"""
        
        try:
            response = self.llm.invoke(prompt)
            result = self._parse_json_response(response.content)
            if result:
                result["success"] = True
                return result
            return {"success": False}
        except Exception as e:
            return {"success": False, "error": str(e)}


# 하위 호환성
class FridgeAnalyzer(ImageAnalyzer):
    def analyze_image(self, image_bytes: bytes) -> Dict:
        return self.analyze_ingredients(image_bytes)
    
    def full_analysis(self, image_bytes: bytes, user_profile=None, meal_type: str = "any") -> Dict:
        analysis = self.analyze_ingredients(image_bytes)
        if not analysis.get("success"):
            return analysis
        
        ingredients = [ing["name"] for ing in analysis.get("ingredients", [])]
        restrictions = []
        if user_profile:
            restrictions = getattr(user_profile, 'allergies', []) + getattr(user_profile, 'diseases', [])
        
        recipes = self.suggest_recipes(ingredients, restrictions, meal_type)
        
        return {
            "success": True,
            "ingredients": analysis.get("ingredients", []),
            "recipes": recipes.get("recipes", []),
            "excluded_ingredients": [r for r in restrictions if r in str(ingredients)]
        }
