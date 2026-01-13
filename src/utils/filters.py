"""
필터링 유틸리티 - 질환/알러지 기반 필터링
"""
from typing import List, Dict, Tuple
from src.models.user_profile import UserProfile, DISEASE_EXCLUSIONS, ALLERGY_EXCLUSIONS


class HealthFilter:
    def __init__(self, user_profile: UserProfile):
        self.profile = user_profile
        self._build_exclusion_lists()
    
    def _build_exclusion_lists(self):
        self.excluded_foods = set()
        self.excluded_keywords = set()
        self.excluded_exercises = set()
        
        for disease in self.profile.diseases:
            if disease in DISEASE_EXCLUSIONS:
                exc = DISEASE_EXCLUSIONS[disease]
                self.excluded_foods.update(exc.get("foods", []))
                self.excluded_keywords.update(exc.get("keywords", []))
                self.excluded_exercises.update(exc.get("exercises", []))
        
        for allergy in self.profile.allergies:
            if allergy in ALLERGY_EXCLUSIONS:
                self.excluded_foods.update(ALLERGY_EXCLUSIONS[allergy])
    
    def filter_food(self, food: Dict) -> Tuple[bool, List[str]]:
        reasons = []
        food_name = food.get("name", "").lower()
        
        for excluded in self.excluded_foods:
            if excluded.lower() in food_name:
                reasons.append(f"'{excluded}' 제외")
        
        return len(reasons) == 0, reasons
    
    def filter_exercise(self, exercise: Dict) -> Tuple[bool, List[str]]:
        reasons = []
        ex_name = exercise.get("name", "").lower()
        
        for excluded in self.excluded_exercises:
            if excluded.lower() in ex_name:
                reasons.append(f"'{excluded}' 제외")
        
        if "관절염" in self.profile.diseases:
            if "고강도" in exercise.get("intensity", ""):
                reasons.append("관절염: 고강도 제외")
        
        return len(reasons) == 0, reasons
    
    def generate_warning_message(self) -> str:
        warnings = []
        if self.profile.diseases:
            warnings.append(f"⚠️ 질환 ({', '.join(self.profile.diseases)}) 고려 중")
        if self.profile.allergies:
            warnings.append(f"🚫 알러지 ({', '.join(self.profile.allergies)}) 제외됨")
        return "\n".join(warnings)
