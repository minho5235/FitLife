"""
이미지 분석 모듈 v2.4 (완성된 음식 분석 + 하위 호환성 FridgeAnalyzer 포함)
"""
import base64
import json
import re
from typing import List, Dict, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from src.config import GOOGLE_API_KEY

class ImageAnalyzer:
    """통합 이미지 분석기 - 식재료 & 운동기구 & 완성된 음식"""
    
    def __init__(self):
        self.vision_model = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=GOOGLE_API_KEY,
            temperature=0.1
        )
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=GOOGLE_API_KEY,
            temperature=0.7
        )
    
    def _encode_image(self, image_bytes: bytes) -> str:
        return base64.b64encode(image_bytes).decode("utf-8")
    
    def _clean_json_text(self, text: str) -> str:
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        return text.replace("\xa0", " ").strip()

    def _parse_json_response(self, text: str) -> Dict:
        cleaned_text = self._clean_json_text(text)
        try:
            return json.loads(cleaned_text)
        except:
            try:
                match = re.search(r'\{.*\}', text, re.DOTALL)
                if match:
                    return json.loads(self._clean_json_text(match.group()))
            except:
                pass
        return {}

    # 1. 식재료 분석 (요리 재료용)
    def analyze_ingredients(self, image_bytes: bytes) -> Dict:
        image_data = self._encode_image(image_bytes)
        prompt = """
        Identify raw ingredients in this image. Output JSON in KOREAN.
        Format: {"ingredients": [{"name": "재료명(한글)", "quantity": "수량", "freshness": "신선/보통"}], "total_confidence": 0.9}
        """
        message = HumanMessage(content=[{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}])
        try:
            response = self.vision_model.invoke([message])
            result = self._parse_json_response(response.content)
            if result: result["success"] = True
            return result or {"success": False, "ingredients": []}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # 2. 완성된 음식 분석 (영양 분석용)
    def analyze_cooked_food(self, image_bytes: bytes, user_profile: str = "") -> Dict:
        image_data = self._encode_image(image_bytes)
        
        prompt = f"""
        이 사진은 '완성된 음식(Meal)'입니다. 
        사용자의 건강 정보: {user_profile}

        이 음식을 분석하여 다음 정보를 **반드시 한글로** JSON 포맷에 맞춰 출력하세요.
        
        JSON Format:
        {{
            "food_name": "음식명",
            "calories": 0,
            "nutrients": {{
                "carbs": "0g", "protein": "0g", "fat": "0g", "sodium": "0mg", "sugar": "0g"
            }},
            "health_analysis": "당뇨가 있으시므로...",
            "eating_guide": "국물은 남기시고...",
            "better_choice": "대안 메뉴"
        }}
        """
        
        message = HumanMessage(content=[{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}])
        
        try:
            response = self.vision_model.invoke([message])
            result = self._parse_json_response(response.content)
            if result: 
                result["success"] = True
                return result
            return {"success": False, "error": "분석 실패"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # 3. 레시피 추천
    def suggest_recipes(self, ingredients: List[str], dietary_restrictions: List[str] = None) -> Dict:
        restrictions_text = f"제외: {', '.join(dietary_restrictions)}" if dietary_restrictions else ""
        prompt = f"""재료: {', '.join(ingredients)}. {restrictions_text}. 한국 요리 3개 추천. JSON 포맷 (한글).
        Format: {{"recipes": [{{"name": "요리명", "description": "설명", "nutrition": {{"calories": 0, "protein": 0}}, "steps": ["1", "2"]}}]}}"""
        try:
            response = self.llm.invoke(prompt)
            result = self._parse_json_response(response.content)
            if result: result["success"] = True
            return result or {"success": False}
        except: return {"success": False}

    # 4. 운동기구 분석
    def analyze_equipment(self, image_bytes: bytes) -> Dict:
        image_data = self._encode_image(image_bytes)
        prompt = """Analyze gym equipment. Output JSON in KOREAN. 
        Format: {"equipment": [{"name": "기구명", "category": "유산소/웨이트"}], "environment": "장소"}"""
        message = HumanMessage(content=[{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}])
        try:
            response = self.vision_model.invoke([message])
            result = self._parse_json_response(response.content)
            if result: result["success"] = True
            return result or {"success": False}
        except: return {"success": False}

    def suggest_exercises(self, equipment: List[str], target_area: str = "전신", duration: int = 30) -> Dict:
        prompt = f"기구: {equipment}, 부위: {target_area}, 시간: {duration}분. 운동 루틴 추천. JSON (한글)."
        try:
            response = self.llm.invoke(prompt)
            result = self._parse_json_response(response.content)
            if result: result["success"] = True
            return result or {"success": False}
        except: return {"success": False}

    # Wrapper (비동기 호환)
    async def analyze_image(self, image_bytes: bytes, mode: str = "general", user_profile: str = "") -> Dict:
        if mode == "meal":
            return self.analyze_cooked_food(image_bytes, user_profile)
        elif mode == "ingredients":
            return self.analyze_ingredients(image_bytes)
        elif mode == "equipment":
            return self.analyze_equipment(image_bytes)
        return {"success": False}


# ★ [핵심 수정] 이 클래스가 없어서 에러가 났던 것입니다.
# 기존 코드와의 호환성을 위해 ImageAnalyzer를 상속받은 껍데기 클래스를 만들어줍니다.
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
        
        recipes = self.suggest_recipes(ingredients, restrictions)
        
        return {
            "success": True,
            "ingredients": analysis.get("ingredients", []),
            "recipes": recipes.get("recipes", []),
            "excluded_ingredients": [r for r in restrictions if r in str(ingredients)]
        }