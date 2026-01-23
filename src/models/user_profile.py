"""
사용자 프로필 모델
질환, 알러지, 건강 목표 등 개인 맞춤 정보 관리
"""
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum


class Disease(Enum):
    DIABETES = "당뇨"
    HYPERTENSION = "고혈압"
    HYPERLIPIDEMIA = "고지혈증"
    GASTRITIS = "위염"
    ARTHRITIS = "관절염"
    KIDNEY_DISEASE = "신장질환"
    GOUT = "통풍"


class Allergy(Enum):
    NUTS = "견과류"
    SHELLFISH = "갑각류"
    DAIRY = "유제품"
    GLUTEN = "글루텐"
    EGGS = "계란"
    SOY = "대두"
    FISH = "생선"


@dataclass
class UserProfile:
    user_id: str = ""
    name: str = ""
    age: int = 30
    gender: str = "남성"
    height: float = 170.0
    weight: float = 70.0
    diseases: List[str] = field(default_factory=list)
    allergies: List[str] = field(default_factory=list)
    medications: List[str] = field(default_factory=list)
    activity_level: str = "보통"
    sleep_hours: float = 7.0
    stress_level: int = 5
    water_intake: float = 1.5
    calories: int = 2000
    protein: float = 60.0
    carbs: float = 300.0
    fat: float = 65.0
    goal: str = "건강유지"
    target_weight: Optional[float] = None
    notes: str = ""
    
    @property
    def bmi(self) -> float:
        height_m = self.height / 100
        return round(self.weight / (height_m ** 2), 1)
    
    @property
    def bmi_status(self) -> str:
        bmi = self.bmi
        if bmi < 18.5: return "저체중"
        elif bmi < 23: return "정상"
        elif bmi < 25: return "과체중"
        else: return "비만"
    
    @property
    def recommended_calories(self) -> int:
        if self.gender == "남성":
            bmr = 88.362 + (13.397 * self.weight) + (4.799 * self.height) - (5.677 * self.age)
        else:
            bmr = 447.593 + (9.247 * self.weight) + (3.098 * self.height) - (4.330 * self.age)
        
        multipliers = {"비활동적": 1.2, "가벼움": 1.375, "보통": 1.55, "활발함": 1.725, "매우활발함": 1.9}
        tdee = bmr * multipliers.get(self.activity_level, 1.55)
        
        if self.goal == "체중감량": return int(tdee - 500)
        elif self.goal == "근육증가": return int(tdee + 300)
        return int(tdee)


# 질환별 제외 목록
DISEASE_EXCLUSIONS = {
    "당뇨": {"foods": ["설탕", "사탕", "케이크", "아이스크림", "콜라"], "keywords": ["고당", "당류"], "exercises": []},
    "고혈압": {"foods": ["라면", "젓갈", "장아찌", "햄", "소시지"], "keywords": ["고나트륨", "고염"], "exercises": ["고강도 웨이트"]},
    "고지혈증": {"foods": ["삼겹살", "곱창", "버터", "튀김"], "keywords": ["고지방", "콜레스테롤"], "exercises": []},
    "위염": {"foods": ["커피", "술", "탄산음료", "매운음식"], "keywords": ["자극적"], "exercises": []},
    "관절염": {"foods": [], "keywords": [], "exercises": ["달리기", "점프", "고강도"]},
}

ALLERGY_EXCLUSIONS = {
    "견과류": ["아몬드", "호두", "땅콩", "캐슈넛", "잣"],
    "갑각류": ["새우", "게", "랍스터", "가재"],
    "유제품": ["우유", "치즈", "요거트", "버터", "아이스크림"],
    "글루텐": ["빵", "파스타", "국수", "쿠키"],
    "계란": ["계란", "마요네즈"],
    "대두": ["두부", "된장", "두유", "콩나물"],
    "생선": ["연어", "고등어", "참치", "멸치"]
}

DISEASE_RECOMMENDATIONS = {
    "당뇨": {"foods": ["닭가슴살", "두부", "브로콜리", "현미"], "exercises": ["걷기", "수영", "자전거"]},
    "고혈압": {"foods": ["바나나", "시금치", "고구마", "연어"], "exercises": ["걷기", "수영", "요가"]},
    "고지혈증": {"foods": ["연어", "고등어", "귀리", "아몬드"], "exercises": ["걷기", "달리기", "수영"]},
    "관절염": {"foods": ["연어", "올리브오일", "브로콜리"], "exercises": ["수영", "자전거", "요가"]}
}
