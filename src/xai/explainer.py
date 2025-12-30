"""
XAI 모듈 - 설명 가능한 AI
SHAP을 활용한 추천 이유 분석
"""
import shap
import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from sklearn.ensemble import RandomForestClassifier
import json


class HealthExplainer:
    """건강 추천 설명 생성기"""
    
    def __init__(self):
        # 건강 지표 피처 정의
        self.feature_names = [
            "단백질_섭취율",
            "탄수화물_섭취율", 
            "지방_섭취율",
            "칼로리_섭취율",
            "수면_시간",
            "운동_빈도",
            "스트레스_수준",
            "수분_섭취량",
            "BMI"
        ]
        
        # 피처별 한글 설명
        self.feature_descriptions = {
            "단백질_섭취율": "단백질 섭취",
            "탄수화물_섭취율": "탄수화물 섭취",
            "지방_섭취율": "지방 섭취",
            "칼로리_섭취율": "칼로리 섭취",
            "수면_시간": "수면 시간",
            "운동_빈도": "운동 빈도",
            "스트레스_수준": "스트레스 수준",
            "수분_섭취량": "수분 섭취",
            "BMI": "체질량지수(BMI)"
        }
        
        # 모델 (실제로는 학습된 모델 로드)
        self.model = None
        self.explainer = None
    
    def analyze_health_factors(self, user_data: Dict) -> Dict:
        """
        사용자 건강 데이터 분석 및 주요 요인 파악
        
        Args:
            user_data: {
                "protein_intake": 50,  # 단백질 (g)
                "carb_intake": 300,    # 탄수화물 (g)
                "fat_intake": 70,      # 지방 (g)
                "calories": 2000,      # 칼로리
                "sleep_hours": 6,      # 수면 시간
                "exercise_days": 2,    # 주당 운동 일수
                "stress_level": 7,     # 스트레스 (1-10)
                "water_intake": 1.5,   # 물 섭취 (L)
                "height": 175,         # 키 (cm)
                "weight": 78           # 체중 (kg)
            }
            
        Returns:
            분석 결과 및 기여도
        """
        # 정규화된 피처 값 계산
        features = self._normalize_features(user_data)
        
        # 규칙 기반 분석 (SHAP 대신 간단한 규칙)
        analysis = self._rule_based_analysis(user_data, features)
        
        return analysis
    
    def _normalize_features(self, user_data: Dict) -> Dict:
        """피처 정규화"""
        # 권장량 기준
        recommended = {
            "protein": user_data.get("weight", 70) * 1.0,  # 체중 * 1g
            "carb": 300,
            "fat": 65,
            "calories": 2000,
            "sleep": 7,
            "exercise": 3,
            "stress": 5,
            "water": 2.0
        }
        
        # BMI 계산
        height_m = user_data.get("height", 170) / 100
        weight = user_data.get("weight", 70)
        bmi = weight / (height_m ** 2)
        
        return {
            "단백질_섭취율": user_data.get("protein_intake", 0) / recommended["protein"],
            "탄수화물_섭취율": user_data.get("carb_intake", 0) / recommended["carb"],
            "지방_섭취율": user_data.get("fat_intake", 0) / recommended["fat"],
            "칼로리_섭취율": user_data.get("calories", 0) / recommended["calories"],
            "수면_시간": user_data.get("sleep_hours", 0) / recommended["sleep"],
            "운동_빈도": user_data.get("exercise_days", 0) / recommended["exercise"],
            "스트레스_수준": user_data.get("stress_level", 5) / 10,
            "수분_섭취량": user_data.get("water_intake", 0) / recommended["water"],
            "BMI": bmi
        }
    
    def _rule_based_analysis(self, user_data: Dict, features: Dict) -> Dict:
        """규칙 기반 건강 분석"""
        issues = []
        contributions = []
        recommendations = []
        
        # 단백질 분석
        if features["단백질_섭취율"] < 0.8:
            deficit = (1 - features["단백질_섭취율"]) * 100
            issues.append("단백질 섭취 부족")
            contributions.append({
                "factor": "단백질 섭취",
                "value": f"{features['단백질_섭취율']*100:.0f}%",
                "impact": round(min(deficit / 100, 0.5), 2),
                "direction": "negative"
            })
            recommendations.append("고단백 식품(닭가슴살, 계란, 두부) 섭취 권장")
        
        # 수면 분석
        if features["수면_시간"] < 0.85:
            issues.append("수면 부족")
            contributions.append({
                "factor": "수면 시간",
                "value": f"{user_data.get('sleep_hours', 0)}시간",
                "impact": round((1 - features["수면_시간"]) * 0.4, 2),
                "direction": "negative"
            })
            recommendations.append("하루 7-8시간 수면 권장")
        
        # 운동 분석
        if features["운동_빈도"] < 0.67:
            issues.append("운동 부족")
            contributions.append({
                "factor": "운동 빈도",
                "value": f"주 {user_data.get('exercise_days', 0)}회",
                "impact": round((1 - features["운동_빈도"]) * 0.35, 2),
                "direction": "negative"
            })
            recommendations.append("주 3회 이상 운동 권장")
        
        # 스트레스 분석
        if features["스트레스_수준"] > 0.7:
            issues.append("스트레스 높음")
            contributions.append({
                "factor": "스트레스 수준",
                "value": f"{user_data.get('stress_level', 5)}/10",
                "impact": round((features["스트레스_수준"] - 0.5) * 0.3, 2),
                "direction": "negative"
            })
            recommendations.append("스트레스 관리(명상, 가벼운 산책) 권장")
        
        # BMI 분석
        bmi = features["BMI"]
        if bmi < 18.5:
            issues.append("저체중")
            contributions.append({
                "factor": "BMI",
                "value": f"{bmi:.1f}",
                "impact": 0.25,
                "direction": "negative"
            })
            recommendations.append("균형 잡힌 영양 섭취로 체중 증가 권장")
        elif bmi > 25:
            issues.append("과체중")
            contributions.append({
                "factor": "BMI",
                "value": f"{bmi:.1f}",
                "impact": round((bmi - 25) * 0.05, 2),
                "direction": "negative"
            })
            recommendations.append("칼로리 조절과 유산소 운동 권장")
        
        # 수분 분석
        if features["수분_섭취량"] < 0.75:
            issues.append("수분 섭취 부족")
            contributions.append({
                "factor": "수분 섭취",
                "value": f"{user_data.get('water_intake', 0)}L",
                "impact": round((1 - features["수분_섭취량"]) * 0.2, 2),
                "direction": "negative"
            })
            recommendations.append("하루 2L 이상 물 섭취 권장")
        
        # 전체 건강 점수 계산
        health_score = 100
        for contrib in contributions:
            health_score -= contrib["impact"] * 100
        health_score = max(0, min(100, health_score))
        
        # 기여도 정렬 (영향도 큰 순)
        contributions.sort(key=lambda x: x["impact"], reverse=True)
        
        return {
            "health_score": round(health_score, 1),
            "status": "양호" if health_score >= 70 else "주의" if health_score >= 50 else "개선필요",
            "issues": issues,
            "contributions": contributions,
            "recommendations": recommendations,
            "raw_features": features
        }
    
    def generate_explanation(self, analysis: Dict) -> str:
        """
        분석 결과를 자연어 설명으로 변환
        """
        lines = []
        
        # 종합 점수
        lines.append(f"📊 **건강 종합 점수: {analysis['health_score']}점** ({analysis['status']})")
        lines.append("")
        
        # 주요 문제점
        if analysis["issues"]:
            lines.append("⚠️ **주요 개선 필요 사항:**")
            for issue in analysis["issues"]:
                lines.append(f"  - {issue}")
            lines.append("")
        
        # 영향 요인
        if analysis["contributions"]:
            lines.append("📈 **영향 요인 분석:**")
            for contrib in analysis["contributions"][:5]:
                impact_pct = contrib["impact"] * 100
                emoji = "🔴" if impact_pct > 20 else "🟡" if impact_pct > 10 else "🟢"
                lines.append(
                    f"  {emoji} {contrib['factor']}: {contrib['value']} "
                    f"(영향도: {impact_pct:.0f}%)"
                )
            lines.append("")
        
        # 추천 사항
        if analysis["recommendations"]:
            lines.append("💡 **추천 사항:**")
            for i, rec in enumerate(analysis["recommendations"], 1):
                lines.append(f"  {i}. {rec}")
        
        return "\n".join(lines)


# 테스트용
if __name__ == "__main__":
    explainer = HealthExplainer()
    
    # 테스트 데이터
    test_user = {
        "protein_intake": 40,
        "carb_intake": 350,
        "fat_intake": 80,
        "calories": 2200,
        "sleep_hours": 5,
        "exercise_days": 1,
        "stress_level": 8,
        "water_intake": 1.0,
        "height": 175,
        "weight": 82
    }
    
    analysis = explainer.analyze_health_factors(test_user)
    explanation = explainer.generate_explanation(analysis)
    
    print(explanation)
